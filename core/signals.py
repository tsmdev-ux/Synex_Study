from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from allauth.account.signals import email_confirmed

from .emails import send_welcome_email


@receiver(user_logged_in)
def mark_first_login(sender, user, request, **kwargs):
    if user.last_login is None:
        request.session['synex_first_login'] = True


@receiver(email_confirmed)
def send_welcome_after_confirmation(request, email_address, **kwargs):
    user = email_address.user
    send_welcome_email(user)
