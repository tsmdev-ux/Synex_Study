from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import SessaoEstudo, Tarefa

User = get_user_model()


def send_welcome_email(user: User):
    """
    Email simples de boas-vindas com call-to-action para registrar primeira tarefa e sessao.
    """
    if not user.email:
        return

    subject = "Bem-vindo ao Synex Study Flow"
    message = (
        f"Olá, {user.username}!\n\n"
        "Sua conta foi criada com sucesso. Aqui vão 3 passos rápidos:\n"
        "1) Crie 1 tarefa no Kanban.\n"
        "2) Defina uma entrega no Cronograma.\n"
        "3) Registre 15 minutos de estudo.\n\n"
        "Dica: use o código PREMIUM-DEMO em /upgrade para testar os recursos completos.\n\n"
        "Bons estudos!\nTime Synex"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_engagement_nudge(user: User, tasks_due=None, inactive_days=None):
    """
    Email de reengajamento: lembra prazos e inatividade de estudo.
    tasks_due: queryset/list de tarefas (opcional)
    inactive_days: int com dias sem registrar sessão (opcional)
    """
    if not user.email:
        return

    lines = [f"Olá, {user.username}!"]

    if tasks_due:
        lines.append("Estas tarefas vencem em breve:")
        for t in tasks_due:
            materia = f"[{t.materia.nome}] " if t.materia else ""
            prazo = t.data_entrega.strftime("%d/%m") if t.data_entrega else "sem data"
            lines.append(f" - {materia}{t.titulo} (vence em {prazo})")
        lines.append("")

    if inactive_days is not None and inactive_days > 0:
        lines.append(f"Você está há {inactive_days} dia(s) sem registrar estudo.")
        lines.append("Abra o dashboard e logue 15 minutos para manter o ritmo.")
        lines.append("")

    if not tasks_due and inactive_days is None:
        return  # nada a dizer

    lines.append("Acesse o cronograma para ajustar prazos e o modo foco para começar.")
    lines.append("Bons estudos!\nTime Synex")

    send_mail(
        subject="Lembrete rápido do Synex",
        message="\n".join(lines),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_payment_receipt(user: User, amount: str, plan: str, next_charge_date=None):
    """
    Recibo simples de pagamento/ativação de plano.
    """
    if not user.email:
        return

    lines = [
        f"Olá, {user.username}!",
        f"Seu plano {plan} foi ativado.",
        f"Valor cobrado: {amount}.",
    ]
    if next_charge_date:
        lines.append(f"Próxima cobrança prevista em: {next_charge_date.strftime('%d/%m/%Y')}.")
    lines.append("")
    lines.append("Obrigado por apoiar o Synex! Qualquer dúvida, é só responder este email.")

    send_mail(
        subject=f"Recibo do plano {plan}",
        message="\n".join(lines),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_cancellation_email(user: User, plan: str):
    """
    Confirma cancelamento/downgrade.
    """
    if not user.email:
        return

    message = (
        f"Olá, {user.username}!\n\n"
        f"O plano {plan} foi cancelado/downgrade solicitado.\n"
        "Você continua no plano Free e pode reativar quando quiser em /upgrade.\n\n"
        "Conta com a gente!\nTime Synex"
    )

    send_mail(
        subject=f"Confirmação de cancelamento - {plan}",
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_trial_reminder(user: User, days_left: int):
    """
    Lembrete de fim de trial/demo.
    """
    if not user.email or days_left < 0:
        return

    message = (
        f"Olá, {user.username}!\n\n"
        f"Seu período de teste termina em {days_left} dia(s).\n"
        "Acesse /upgrade para manter o plano Premium sem interrupções.\n\n"
        "Bons estudos!\nTime Synex"
    )

    send_mail(
        subject="Seu trial está terminando",
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


def get_users_needing_engagement():
    """
    Retorna users com tarefas próximas do prazo ou inativos em sessões de estudo.
    - Prazos: tarefas em aberto vencendo em 3 dias.
    - Inatividade: nenhuma sessão nos últimos 7 dias.
    """
    now = timezone.now().date()
    soon = now + timedelta(days=3)
    inactive_since = now - timedelta(days=7)

    users_with_due = (
        User.objects.filter(tarefa__status__in=["todo", "doing", "review"], tarefa__data_entrega__lte=soon)
        .distinct()
        .exclude(email__isnull=True)
        .exclude(email="")
    )

    users_inactive = (
        User.objects.exclude(email__isnull=True)
        .exclude(email="")
        .exclude(sessoes__data__gte=inactive_since)
    )

    return users_with_due.union(users_inactive)


def build_engagement_payload(user: User):
    """
    Monta dados para o email de nudge: lista de tarefas e dias de inatividade.
    """
    now = timezone.now().date()
    soon = now + timedelta(days=3)
    inactive_since = now - timedelta(days=7)

    tasks_due = list(
        Tarefa.objects.filter(
            usuario=user, status__in=["todo", "doing", "review"], data_entrega__isnull=False, data_entrega__lte=soon
        ).order_by("data_entrega")[:5]
    )

    last_session = (
        SessaoEstudo.objects.filter(usuario=user).order_by("-data").values_list("data", flat=True).first()
    )
    inactive_days = None
    if last_session:
        delta = (now - last_session).days
        inactive_days = delta if delta >= 7 else None
    else:
        inactive_days = 7  # nunca registrou

    return tasks_due, inactive_days
