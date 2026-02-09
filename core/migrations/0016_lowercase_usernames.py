from django.db import migrations


def normalize_usernames(apps, schema_editor):
    User = apps.get_model("auth", "User")
    users = list(User.objects.all().only("id", "username"))

    bucket = {}
    for user in users:
        normalized = (user.username or "").strip().lower()
        bucket.setdefault(normalized, []).append(user)

    conflicts = {key: vals for key, vals in bucket.items() if key and len(vals) > 1}
    if conflicts:
        conflict_list = []
        for key, vals in conflicts.items():
            ids = ",".join(str(v.id) for v in vals)
            conflict_list.append(f"{key}: [{ids}]")
        raise RuntimeError(
            "Conflito ao normalizar usernames. Resolva antes de migrar: "
            + "; ".join(conflict_list)
        )

    for user in users:
        normalized = (user.username or "").strip().lower()
        if user.username != normalized:
            user.username = normalized
            user.save(update_fields=["username"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_merge_0014_feedback_notifications"),
    ]

    operations = [
        migrations.RunPython(normalize_usernames, migrations.RunPython.noop),
    ]

