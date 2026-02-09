from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_normalizacao_indices"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("review_overdue_enabled", models.BooleanField(default=True)),
                (
                    "review_overdue_days",
                    models.PositiveSmallIntegerField(
                        default=3,
                        validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(30)],
                    ),
                ),
                (
                    "usuario",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_settings", to="auth.user"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(default="review_overdue", max_length=32)),
                ("title", models.CharField(max_length=120)),
                ("message", models.TextField()),
                ("event_key", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tarefa",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="core.tarefa"),
                ),
                (
                    "usuario",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="auth.user"),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["usuario", "read_at"], name="idx_notif_user_read"),
                    models.Index(fields=["usuario", "created_at"], name="idx_notif_user_created"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(fields=("usuario", "event_key"), name="uniq_notif_user_event"),
        ),
    ]

