from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(user_logged_in)
def mark_first_login(sender, user, request, **kwargs):
    # Sempre marca o login na sessão; o frontend controla se já foi exibido no dispositivo.
    request.session['synex_first_login'] = True


@receiver(pre_save, sender=User)
def normalize_username(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.strip().lower()
