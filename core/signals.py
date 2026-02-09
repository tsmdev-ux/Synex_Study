from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def mark_first_login(sender, user, request, **kwargs):
    if user.last_login is None:
        request.session['synex_first_login'] = True
