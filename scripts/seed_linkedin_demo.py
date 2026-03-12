from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Anotacao, Materia, MetaObjetivo, SessaoEstudo, Tarefa


USERNAME = "linkedin_demo"
PASSWORD = "SynexDemo123!"
EMAIL = "linkedin-demo@synex.local"


def run() -> None:
    user, created = User.objects.get_or_create(
        username=USERNAME,
        defaults={"email": EMAIL},
    )
    if created:
        user.set_password(PASSWORD)
        user.save(update_fields=["password"])
    elif not user.check_password(PASSWORD):
        user.set_password(PASSWORD)
        user.save(update_fields=["password"])

    # Limpa dados antigos para manter os prints consistentes.
    SessaoEstudo.objects.filter(usuario=user).delete()
    Anotacao.objects.filter(usuario=user).delete()
    Tarefa.objects.filter(usuario=user).delete()
    MetaObjetivo.objects.filter(usuario=user).delete()
    Materia.objects.filter(usuario=user).delete()

    materias = [
        Materia.objects.create(usuario=user, nome="Backend", cor="#3B82F6", descricao="API e arquitetura Django"),
        Materia.objects.create(usuario=user, nome="Frontend", cor="#10B981", descricao="UI e interacoes"),
        Materia.objects.create(usuario=user, nome="Banco de Dados", cor="#F59E0B", descricao="SQL e modelagem"),
    ]

    meta = MetaObjetivo.objects.create(
        usuario=user,
        titulo="Finalizar release do Synex",
        descricao="Concluir backlog, revisar seguranca e preparar demonstracao.",
        data_alvo=timezone.localdate() + timedelta(days=21),
    )

    tarefas = [
        ("Ajustar headers de seguranca", "done", "A", 1, 2),
        ("Refinar tela de cronograma", "doing", "M", 2, 4),
        ("Implementar filtros no dashboard", "review", "M", 3, 5),
        ("Criar testes de regras premium", "todo", "A", 4, 7),
        ("Documentar fluxo de onboarding", "todo", "B", 5, 10),
        ("Melhorar feedback visual do kanban", "doing", "M", 6, 6),
        ("Adicionar exportacao de tarefas", "done", "A", 7, 1),
    ]

    tarefa_objs = []
    for i, (titulo, status, prioridade, ordem, days_from_now) in enumerate(tarefas):
        t = Tarefa.objects.create(
            usuario=user,
            materia=materias[i % len(materias)],
            meta=meta,
            titulo=titulo,
            descricao="Item gerado para screenshots do LinkedIn.",
            status=status,
            prioridade=prioridade,
            ordem=ordem,
            data_entrega=timezone.localdate() + timedelta(days=days_from_now),
        )
        tarefa_objs.append(t)

    nota1 = Anotacao.objects.create(
        usuario=user,
        materia=materias[0],
        titulo="Checklist de seguranca",
        conteudo="Aplicar CSRF, validar input e revisar permissoes por usuario.",
        favorito=True,
        prioridade="A",
        fonte="https://docs.djangoproject.com/en/6.0/topics/security/",
    )
    nota1.tags.add("seguranca", "django")

    nota2 = Anotacao.objects.create(
        usuario=user,
        materia=materias[1],
        titulo="UX do cronograma",
        conteudo="Melhorias visuais para visualizacao semanal e mensal.",
        favorito=False,
        prioridade="M",
    )
    nota2.tags.add("ux", "cronograma")

    today = timezone.localdate()
    session_pattern = [25, 35, 45, 40, 60, 30, 50, 55, 20, 48]
    for offset, minutes in enumerate(session_pattern):
        SessaoEstudo.objects.create(
            usuario=user,
            materia=materias[offset % len(materias)],
            tarefa=tarefa_objs[offset % len(tarefa_objs)],
            duracao_min=minutes,
            data=today - timedelta(days=(len(session_pattern) - 1 - offset)),
        )

    perfil = user.perfil
    perfil.is_premium = True
    perfil.premium_activated_at = timezone.now() - timedelta(days=12)
    perfil.premium_expires_at = timezone.now() + timedelta(days=18)
    perfil.save(update_fields=["is_premium", "premium_activated_at", "premium_expires_at"])

    print("seed-ok")
    print(f"username={USERNAME}")
    print(f"password={PASSWORD}")


run()
