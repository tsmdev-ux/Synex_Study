from datetime import timedelta
import json
import logging

import markdown
import bleach
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDay
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

from .emails import send_cancellation_email, send_payment_receipt, send_welcome_email
from .forms import (
    AnotacaoForm,
    MateriaForm,
    MetaForm,
    SessaoEstudoForm,
    TarefaForm,
    PerfilForm,
    SignupForm,
)
from .models import (
    Anotacao,
    Materia,
    MetaObjetivo,
    SessaoEstudo,
    Tarefa,
    Perfil,
    Payment,
    Subscription,
    Feedback,
    NotificationSetting,
    Notification,
)
from .payments import create_abacate_checkout, cancel_abacate_subscription, handle_abacate_webhook, AbacatePayError

logger = logging.getLogger(__name__)


def _get_notification_settings(user):
    settings_obj, _ = NotificationSetting.objects.get_or_create(usuario=user)
    return settings_obj


def _ensure_review_overdue_notifications(user, settings_obj):
    if not settings_obj.review_overdue_enabled:
        return
    days = settings_obj.review_overdue_days or 3
    threshold = timezone.now() - timedelta(days=days)
    tarefas = Tarefa.objects.filter(usuario=user, status='review', updated_at__lte=threshold)
    for tarefa in tarefas:
        event_key = f"review_overdue:{tarefa.id}:{days}"
        Notification.objects.get_or_create(
            usuario=user,
            event_key=event_key,
            defaults={
                "tarefa": tarefa,
                "type": "review_overdue",
                "title": "Tarefa em revisão há muito tempo",
                "message": f'A tarefa "{tarefa.titulo}" está em Revisão há mais de {days} dias.',
            },
        )


def landing_page(request):
    # Se o usuário já estiver logado, manda ele direto pro dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')

def home_redirect(request):
    return redirect('home')



# --- AUTH ---
def cadastro(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            novo_usuario = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Faça login agora.')
            send_welcome_email(novo_usuario)
            return redirect(f"{reverse('login')}?signup=ok")
    else:
        form = SignupForm()

    return render(request, 'core/cadastro.html', {'form': form})


@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto atualizada!')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'core/perfil.html', {'form': form, 'perfil': perfil})


@login_required
@require_POST
def abacate_checkout_view(request):
    kind = request.POST.get("kind", "subscription")
    if kind not in ["subscription", "one_time"]:
        messages.error(request, "Invalid checkout type.")
        return redirect("upgrade")

    if kind == "one_time":
        amount_cents = getattr(settings, "ABACATEPAY_ONE_TIME_PRICE_CENTS", 2990)
        description = "Premium one-time"
    else:
        amount_cents = getattr(settings, "ABACATEPAY_PREMIUM_PRICE_CENTS", 2990)
        description = "Premium subscription"

    currency = getattr(settings, "ABACATEPAY_CURRENCY", "BRL")
    success_url = request.build_absolute_uri(reverse("assinatura"))
    cancel_url = request.build_absolute_uri(reverse("upgrade"))

    try:
        checkout_url = create_abacate_checkout(
            request.user,
            kind=kind,
            amount_cents=amount_cents,
            currency=currency,
            success_url=success_url,
            cancel_url=cancel_url,
            description=description,
        )
    except AbacatePayError as exc:
        messages.error(request, str(exc))
        return redirect("upgrade")

    if checkout_url:
        return redirect(checkout_url)
    messages.success(request, "PIX simulado com sucesso.")
    return redirect("assinatura")


@csrf_exempt
@require_POST
def abacate_webhook(request):
    ok, message = handle_abacate_webhook(request)
    status = 200 if ok else 400
    return JsonResponse({"success": ok, "message": message}, status=status)


@login_required
def upgrade_view(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        promo_code = request.POST.get('code', '').strip()
        expected = getattr(settings, 'PROMO_PREMIUM_CODE', '').strip()
        if promo_code and expected and promo_code.upper() == expected.upper():
            perfil.is_premium = True
            perfil.premium_activated_at = timezone.now()
            perfil.save()
            messages.success(request, 'Código válido! Sua conta agora é Premium.')
            next_charge = perfil.premium_activated_at + timedelta(days=30)
            send_payment_receipt(request.user, amount="R$29,90", plan="Premium", next_charge_date=next_charge)
        else:
            messages.error(request, 'Código inválido. Verifique e tente novamente.')
        return redirect('upgrade')

    # expiração demo
    premium_days = getattr(settings, 'PROMO_PREMIUM_DAYS', 0)
    expires_at = None
    if premium_days and perfil.premium_activated_at:
        expires_at = perfil.premium_activated_at + timezone.timedelta(days=premium_days)
        if expires_at < timezone.now():
            perfil.is_premium = False
            perfil.save()
            messages.warning(request, 'Seu Premium demo expirou. Use o código novamente ou faça upgrade real.')

    debug_code = getattr(settings, 'PROMO_PREMIUM_CODE', None) if settings.DEBUG else None

    return render(request, 'core/upgrade.html', {
        'perfil': perfil,
        'expires_at': expires_at,
        'promo_days': premium_days,
        'debug_code': debug_code,
    })


def _build_assinatura_context(user):
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    subscription = Subscription.objects.filter(usuario=user).order_by('-created_at').first()
    payments = Payment.objects.filter(usuario=user).order_by('-created_at')[:5]

    next_charge = None
    if subscription and subscription.current_period_end:
        next_charge = subscription.current_period_end
    elif perfil.is_premium and perfil.premium_activated_at:
        next_charge = perfil.premium_activated_at + timedelta(days=30)

    history = []
    for pay in payments:
        history.append({
            'title': f'Payment {pay.kind}',
            'date': pay.created_at,
            'amount': f'R${pay.amount_cents / 100:.2f}',
            'status': pay.status,
        })
    if not history and perfil.premium_activated_at:
        history.append({
            'title': 'Premium activated',
            'date': perfil.premium_activated_at,
            'amount': 'R$29,90',
            'status': 'Paid',
        })

    return {
        'perfil': perfil,
        'next_charge': next_charge,
        'history': history,
        'subscription': subscription,
        'payments': payments,
    }


@login_required
def assinatura_view(request):
    return redirect(reverse('configuracoes') + '#assinatura')


# --- KANBAN ---
@login_required
def kanban_view(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    total_tarefas = Tarefa.objects.filter(usuario=request.user).count()
    limite_gratuito = 3
    limite_atingido = (not perfil.is_premium) and total_tarefas >= limite_gratuito

    if request.method == 'POST':
        if limite_atingido:
            messages.warning(request, f'Plano gratuito permite {limite_gratuito} tarefas. Torne-se Premium para criar mais.')
            return redirect('kanban')
        form = TarefaForm(request.POST, user=request.user)
        form.instance.usuario = request.user
        if form.is_valid():
            nova_tarefa = form.save(commit=False)
            nova_tarefa.usuario = request.user
            nova_tarefa.status = 'todo'
            nova_tarefa.save()
            return redirect('kanban')
        messages.error(request, 'Não foi possível salvar. Verifique os campos obrigatórios.')
    else:
        form = TarefaForm(user=request.user)

    tarefas = Tarefa.objects.filter(usuario=request.user)
    sete_dias_atras = timezone.now() - timedelta(days=7)

    context = {
        'todo': tarefas.filter(status='todo').order_by('ordem'),
        'doing': tarefas.filter(status='doing').order_by('ordem'),
        'review': tarefas.filter(status='review').order_by('ordem'),
        'done': tarefas.filter(status='done', updated_at__gte=sete_dias_atras).order_by('-updated_at'),
        'form': form,
        'limite_atingido': limite_atingido,
        'limite_gratuito': limite_gratuito,
        'is_premium': perfil.is_premium,
        'perfil': perfil,
    }
    return render(request, 'core/kanban.html', context)


@login_required
@require_POST
def api_mover_tarefa(request):
    try:
        data = json.loads(request.body)
        tarefa_id = data.get('id')
        novo_status = data.get('status')

        valid_status = {choice[0] for choice in Tarefa.STATUS_CHOICES}
        if novo_status not in valid_status:
            return JsonResponse({'success': False, 'error': 'Status inválido.'}, status=400)

        tarefa = Tarefa.objects.get(id=tarefa_id, usuario=request.user)
        tarefa.status = novo_status
        tarefa.save()

        return JsonResponse({'success': True, 'message': 'Tarefa movida!'})
    except Exception:
        logger.exception("api_mover_tarefa failed")
        return JsonResponse({'success': False, 'error': 'Erro ao mover tarefa.'}, status=500)


# --- ANOTAÇÕES ---
@login_required
def anotacoes_list(request):
    search_query = request.GET.get('q')
    tag_filter = request.GET.get('tag')

    anotacoes = Anotacao.objects.filter(usuario=request.user)

    if search_query:
        anotacoes = anotacoes.filter(
            Q(titulo__icontains=search_query)
            | Q(conteudo__icontains=search_query)
            | Q(tags__name__icontains=search_query)
        ).distinct()

    if tag_filter:
        anotacoes = anotacoes.filter(tags__slug=tag_filter)

    anotacoes = anotacoes.order_by('-prioridade', '-created_at')

    return render(
        request,
        'core/anotacoes_list.html',
        {'anotacoes': anotacoes, 'search_query': search_query},
    )


@login_required
def anotacao_edit(request, id=None):
    anotacao = get_object_or_404(Anotacao, id=id, usuario=request.user) if id else None

    if request.method == 'POST':
        form = AnotacaoForm(request.POST, instance=anotacao, user=request.user)
        if form.is_valid():
            nova_anotacao = form.save(commit=False)
            nova_anotacao.usuario = request.user
            nova_anotacao.save()
            return redirect('anotacoes_list')
    else:
        form = AnotacaoForm(instance=anotacao, user=request.user)

    return render(request, 'core/anotacao_form.html', {'form': form})


@login_required
def anotacao_detail(request, id):
    nota = get_object_or_404(Anotacao, id=id, usuario=request.user)

    html_content = markdown.markdown(nota.conteudo, extensions=['fenced_code', 'tables'])
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
        "p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "blockquote", "hr", "br",
        "table", "thead", "tbody", "tr", "th", "td",
        "a", "span",
    })
    allowed_attrs = {
        "a": ["href", "title", "target", "rel"],
        "span": ["class"],
        "code": ["class"],
        "pre": ["class"],
        "th": ["colspan", "rowspan"],
        "td": ["colspan", "rowspan"],
    }
    html_content = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
    )

    return render(request, 'core/anotacao_detail.html', {'nota': nota, 'html_content': html_content})


@login_required
@require_POST
def anotacao_delete(request, id):
    nota = get_object_or_404(Anotacao, id=id, usuario=request.user)
    nota.delete()
    return redirect('anotacoes_list')


# --- DASHBOARD ---
@login_required
def dashboard_view(request):
    # Criar sessão de estudo
    if request.method == 'POST':
        session_form = SessaoEstudoForm(request.POST, user=request.user)
        session_form.instance.usuario = request.user
        if session_form.is_valid():
            sessao = session_form.save(commit=False)
            sessao.usuario = request.user
            sessao.save()
            messages.success(request, 'Sessão de estudo registrada!')
            return redirect('dashboard')
    else:
        session_form = SessaoEstudoForm(initial={'data': timezone.now().date()}, user=request.user)

    # KPIs de tarefas
    total_tasks = Tarefa.objects.filter(usuario=request.user).count()
    done_tasks = Tarefa.objects.filter(usuario=request.user, status='done').count()
    todo_tasks = Tarefa.objects.filter(usuario=request.user, status='todo').count()
    review_tasks = Tarefa.objects.filter(usuario=request.user, status='review').count()
    completion_rate = int((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Produtividade semanal (tarefas concluídas)
    today = timezone.now().date()
    last_7_days = today - timedelta(days=6)

    productivity_data = (
        Tarefa.objects.filter(usuario=request.user, status='done', updated_at__date__gte=last_7_days)
        .annotate(day=TruncDay('updated_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    dates = [last_7_days + timedelta(days=i) for i in range(7)]
    chart_labels = [date.strftime('%d/%m') for date in dates]
    chart_data = []
    data_dict = {item['day'].date(): item['count'] for item in productivity_data}
    for date in dates:
        chart_data.append(data_dict.get(date, 0))

    # Matérias (rosca)
    materias_data = (
        Tarefa.objects.filter(usuario=request.user)
        .values('materia__nome', 'materia__cor')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    materia_labels = [m['materia__nome'] for m in materias_data]
    materia_counts = [m['total'] for m in materias_data]
    materia_colors = [m['materia__cor'] for m in materias_data]

    proximos_prazos = (
        Tarefa.objects.filter(usuario=request.user, status__in=['todo', 'doing', 'review'], data_entrega__isnull=False)
        .order_by('data_entrega')[:5]
    )

    # Sessões de estudo
    study_total = (
        SessaoEstudo.objects.filter(usuario=request.user).aggregate(total=Sum('duracao_min')).get('total') or 0
    )
    study_today = (
        SessaoEstudo.objects.filter(usuario=request.user, data=today).aggregate(total=Sum('duracao_min')).get('total')
        or 0
    )
    daily_goal_min = 45
    study_goal_progress = int(min(100, (study_today / daily_goal_min * 100))) if daily_goal_min else 0
    session_dates = set(SessaoEstudo.objects.filter(usuario=request.user).values_list('data', flat=True))
    streak_days = 0
    cursor = today
    while cursor in session_dates:
        streak_days += 1
        cursor -= timedelta(days=1)
    study_total_hours = round(study_total / 60, 1) if study_total else 0
    study_today_hours = round(study_today / 60, 1) if study_today else 0
    study_week_raw = (
        SessaoEstudo.objects.filter(usuario=request.user, data__gte=last_7_days)
        .values('data')
        .annotate(total=Sum('duracao_min'))
        .order_by('data')
    )
    study_map = {item['data']: item['total'] for item in study_week_raw}
    study_labels = [d.strftime('%d/%m') for d in dates]
    study_data = [study_map.get(d, 0) for d in dates]
    recent_sessions = (
        SessaoEstudo.objects.filter(usuario=request.user)
        .select_related('materia')
        .order_by('-data', '-created_at')[:5]
    )

    context = {
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'todo_tasks': todo_tasks,
        'review_tasks': review_tasks,
        'completion_rate': completion_rate,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'materia_labels': materia_labels,
        'materia_counts': materia_counts,
        'materia_colors': materia_colors,
        'proximos_prazos': proximos_prazos,
        'session_form': session_form,
        'study_total': study_total,
        'study_today': study_today,
        'study_total_hours': study_total_hours,
        'study_today_hours': study_today_hours,
        'study_labels': study_labels,
        'study_data': study_data,
        'study_goal_min': daily_goal_min,
        'study_goal_progress': study_goal_progress,
        'study_streak_days': streak_days,
        'recent_sessions': recent_sessions,
        'perfil': perfil if 'perfil' in locals() else getattr(request.user, 'perfil', None),
    }
    return render(request, 'core/dashboard.html', context)


# --- OUTROS ---
@login_required
def foco_view(request):
    return render(request, 'core/foco.html')


@login_required
def cronograma_view(request):
    return render(request, 'core/cronograma.html')


@login_required
def api_tarefas_calendar(request):
    if request.method == 'GET':
        tarefas = Tarefa.objects.filter(usuario=request.user, data_entrega__isnull=False)
        eventos = []

        for t in tarefas:
            cor = t.materia.cor if t.materia else '#6b7280'
            duracao = (
                SessaoEstudo.objects.filter(usuario=request.user, tarefa=t)
                .aggregate(total=Sum('duracao_min'))
                .get('total')
                or 0
            )
            eventos.append(
                {
                    'id': t.id,
                    'title': f"{t.materia.nome}: {t.titulo}" if t.materia else t.titulo,
                    'start': t.data_entrega.strftime('%Y-%m-%d'),
                    'backgroundColor': cor,
                    'borderColor': cor,
                    'extendedProps': {'status': t.status, 'duration_min': duracao},
                }
            )
        return JsonResponse(eventos, safe=False)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tarefa_id = data.get('id')
            nova_data = data.get('data')

            tarefa = Tarefa.objects.get(id=tarefa_id, usuario=request.user)
            tarefa.data_entrega = parse_date(nova_data)
            tarefa.save()

            return JsonResponse({'success': True})
        except Exception:
            logger.exception("api_tarefas_calendar update failed")
            return JsonResponse({'success': False, 'error': 'Erro ao atualizar data.'}, status=400)


@login_required
def api_study_calendar(request):
    if request.method != 'GET':
        return JsonResponse([], safe=False)

    # Soma minutos por dia e devolve como eventos all-day
    sessoes = (
        SessaoEstudo.objects.filter(usuario=request.user)
        .values('data')
        .annotate(total_min=Sum('duracao_min'))
        .order_by('data')
    )

    eventos = []
    for s in sessoes:
        horas = round((s['total_min'] or 0) / 60, 1)
        eventos.append({
            'id': f"study-{s['data']}",
            'title': f"{horas}h",
            'start': s['data'].strftime('%Y-%m-%d'),
            'allDay': True,
            'backgroundColor': '#f8fafc',
            'borderColor': '#e5e7eb',
            'textColor': '#111827',
            'classNames': ['study-event'],
            'study_hours': horas,
        })

    return JsonResponse(eventos, safe=False)


@login_required
def metas_list(request):
    if request.method == 'POST':
        form = MetaForm(request.POST)
        if form.is_valid():
            nova_meta = form.save(commit=False)
            nova_meta.usuario = request.user
            nova_meta.save()
            return redirect('metas_list')
    else:
        form = MetaForm()

    metas = MetaObjetivo.objects.filter(usuario=request.user).order_by('data_alvo')

    return render(request, 'core/metas_list.html', {'metas': metas, 'form': form})


@login_required
def meta_detail(request, id):
    meta = get_object_or_404(MetaObjetivo, id=id, usuario=request.user)
    tarefas = meta.tarefas.all().order_by('status', 'data_entrega')
    return render(request, 'core/meta_detail.html', {'meta': meta, 'tarefas': tarefas})


@login_required
@require_POST
def api_toggle_favorito(request):
    try:
        data = json.loads(request.body)
        nota_id = data.get('id')

        nota = Anotacao.objects.get(id=nota_id, usuario=request.user)
        nota.favorito = not nota.favorito
        nota.save()

        return JsonResponse({'success': True, 'is_favorito': nota.favorito})
    except Exception:
        logger.exception("api_toggle_favorito failed")
        return JsonResponse({'success': False}, status=400)


@login_required
def materias_list(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            nova_materia = form.save(commit=False)
            nova_materia.usuario = request.user
            nova_materia.save()
            return redirect('materias_list')
    else:
        form = MateriaForm()

    materias = Materia.objects.filter(usuario=request.user).annotate(total_tarefas=Count('tarefa'))

    return render(request, 'core/materias_list.html', {'materias': materias, 'form': form})


@login_required
@require_POST
def materia_delete(request, id):
    materia = get_object_or_404(Materia, id=id, usuario=request.user)
    materia.delete()
    return redirect('materias_list')


@login_required
def api_export_tarefas(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if not perfil.is_premium:
        return JsonResponse({'success': False, 'error': 'Disponível apenas para Premium.'}, status=403)

    tarefas = []
    for t in Tarefa.objects.filter(usuario=request.user):
        tarefas.append({
            'id': t.id,
            'titulo': t.titulo,
            'status': t.status,
            'status_label': t.get_status_display(),  # Em português: A Fazer, Em Andamento, Revisao, Concluido
            'prioridade': t.prioridade,
            'data_entrega': t.data_entrega,
        })
    return JsonResponse(tarefas, safe=False)


@login_required
@require_POST
def api_feedback(request):
    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads(request.body or "{}")
        else:
            payload = request.POST

        rating_raw = payload.get("rating", "")
        comment = (payload.get("comment") or "").strip()
        page = (payload.get("page") or "").strip()[:255]

        try:
            rating = int(rating_raw)
        except (TypeError, ValueError):
            rating = 0

        if rating < 1 or rating > 5:
            return JsonResponse({"success": False, "error": "Avalie de 1 a 5 estrelas."}, status=400)

        if len(comment) > 5000:
            return JsonResponse({"success": False, "error": "Comentario muito longo."}, status=400)

        feedback = Feedback.objects.create(
            usuario=request.user,
            rating=rating,
            comment=comment,
            page=page,
        )
        # Envia email de notificação (best-effort)
        try:
            to_email = getattr(settings, "FEEDBACK_EMAIL_TO", "") or getattr(settings, "EMAIL_HOST_USER", "")
            if to_email:
                subject = f"Novo feedback: {rating} estrelas"
                body = (
                    f"Usuario: {request.user.username}\n"
                    f"Email: {request.user.email or '-'}\n"
                    f"Pagina: {page or '-'}\n"
                    f"Nota: {rating}\n"
                    f"Comentario:\n{comment or '-'}\n\n"
                    f"Enviado em: {feedback.created_at:%d/%m/%Y %H:%M}"
                )
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=True)
        except Exception:
            logger.exception("api_feedback email failed")
        return JsonResponse({"success": True})
    except Exception:
        logger.exception("api_feedback failed")
        return JsonResponse({"success": False, "error": "Erro ao enviar feedback."}, status=500)


def termos_view(request):
    return render(request, 'core/termos.html')


def privacidade_view(request):
    return render(request, 'core/privacidade.html')


@login_required
def configuracoes_view(request):
    assinatura_ctx = _build_assinatura_context(request.user)
    perfil = assinatura_ctx.get('perfil')
    subscription = assinatura_ctx.get('subscription')
    notification_settings = _get_notification_settings(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_notifications':
            enabled = request.POST.get('review_overdue_enabled') == 'on'
            days_raw = (request.POST.get('review_overdue_days') or '').strip()
            try:
                days = int(days_raw)
            except (TypeError, ValueError):
                days = notification_settings.review_overdue_days or 3
            days = max(1, min(30, days))
            notification_settings.review_overdue_enabled = enabled
            notification_settings.review_overdue_days = days
            notification_settings.save(update_fields=['review_overdue_enabled', 'review_overdue_days'])
            messages.success(request, 'Notificações atualizadas.')
            return redirect(reverse('configuracoes') + '#notificacoes')

        if action == 'cancel':
            if subscription and subscription.provider_id:
                try:
                    cancel_abacate_subscription(subscription)
                    messages.success(request, 'Subscription cancel requested.')
                except AbacatePayError as exc:
                    messages.error(request, str(exc))
                    return redirect(reverse('configuracoes') + '#assinatura')

            if subscription and subscription.current_period_end and subscription.current_period_end > timezone.now():
                perfil.is_premium = True
                perfil.premium_expires_at = subscription.current_period_end
            else:
                perfil.is_premium = False
                perfil.premium_activated_at = None
                perfil.premium_expires_at = None
                send_cancellation_email(request.user, plan='Premium')
            perfil.save(update_fields=['is_premium', 'premium_activated_at', 'premium_expires_at'])
            return redirect(reverse('configuracoes') + '#assinatura')

    context = {'app_version': getattr(settings, 'APP_VERSION', '0.075 beta')}
    context.update(assinatura_ctx)
    context.update({'notification_settings': notification_settings})
    return render(request, 'core/configuracoes.html', context)


@login_required
def feedbacks_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Sem permissao.")
    feedbacks = Feedback.objects.select_related("usuario").order_by("-created_at")
    return render(request, "core/feedbacks.html", {"feedbacks": feedbacks})


@login_required
def api_notifications(request):
    settings_obj = _get_notification_settings(request.user)
    _ensure_review_overdue_notifications(request.user, settings_obj)

    items = Notification.objects.filter(usuario=request.user).order_by('-created_at')[:30]
    unread_count = Notification.objects.filter(usuario=request.user, read_at__isnull=True).count()

    payload = []
    for item in items:
        payload.append({
            "id": item.id,
            "title": item.title,
            "message": item.message,
            "created_at": item.created_at.isoformat(),
            "read": bool(item.read_at),
        })

    return JsonResponse({"items": payload, "unread_count": unread_count})


@login_required
@require_POST
def api_notifications_mark_read(request):
    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads(request.body or "{}")
        else:
            payload = request.POST

        mark_all = payload.get("all") in [True, "true", "1", 1, "on"]
        now = timezone.now()

        if mark_all:
            Notification.objects.filter(usuario=request.user, read_at__isnull=True).update(read_at=now)
            return JsonResponse({"success": True})

        ids = payload.get("ids") or []
        if isinstance(ids, str):
            ids = [i for i in ids.split(",") if i.strip()]
        Notification.objects.filter(usuario=request.user, id__in=ids).update(read_at=now)
        return JsonResponse({"success": True})
    except Exception:
        logger.exception("api_notifications_mark_read failed")
        return JsonResponse({"success": False, "error": "Erro ao atualizar notificações."}, status=500)


def service_worker(request):
    sw_path = settings.BASE_DIR / "core" / "static" / "core" / "sw.js"
    if sw_path.exists():
        content = sw_path.read_text(encoding="utf-8")
    else:
        content = ""
    response = HttpResponse(content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def manutencao_view(request):
    if not getattr(settings, 'MAINTENANCE_MODE', False):
        return redirect('home')
    context = {
        'maintenance_message': getattr(settings, 'MAINTENANCE_MESSAGE', ''),
        'maintenance_end_at': getattr(settings, 'MAINTENANCE_END_AT', ''),
    }
    return render(request, 'core/manutencao.html', context)
