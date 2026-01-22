from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from core.emails import build_engagement_payload, get_users_needing_engagement, send_engagement_nudge


class Command(BaseCommand):
    help = "Envia emails de reengajamento para usuários com prazos próximos ou sem sessões recentes."

    def handle(self, *args, **options):
        users = get_users_needing_engagement()
        total_sent = 0

        for user in users:
            tasks_due, inactive_days = build_engagement_payload(user)
            if not tasks_due and inactive_days is None:
                continue
            send_engagement_nudge(user, tasks_due=tasks_due, inactive_days=inactive_days)
            total_sent += 1
            self.stdout.write(self.style.SUCCESS(f"Email enviado para {user.email}"))

        self.stdout.write(self.style.NOTICE(f"Total de emails enviados: {total_sent}"))
