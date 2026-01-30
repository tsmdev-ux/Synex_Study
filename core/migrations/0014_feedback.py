from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_normalizacao_indices"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("comment", models.TextField(blank=True)),
                ("page", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
