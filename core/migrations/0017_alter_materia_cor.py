from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_lowercase_usernames"),
    ]

    operations = [
        migrations.AlterField(
            model_name="materia",
            name="cor",
            field=models.CharField(default="#3B82F6", max_length=7),
        ),
    ]

