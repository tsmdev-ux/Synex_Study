from django.utils import timezone
from .models import Anotacao, Perfil

def _sync_premium(perfil):
    if not perfil:
        return
    if perfil.is_premium and perfil.premium_expires_at and perfil.premium_expires_at <= timezone.now():
        perfil.is_premium = False
        perfil.premium_activated_at = None
        perfil.premium_expires_at = None
        perfil.save(update_fields=["is_premium", "premium_activated_at", "premium_expires_at"])



def favoritos_globais(request):
    perfil = None
    if request.user.is_authenticated:
        favoritos = Anotacao.objects.filter(usuario=request.user, favorito=True).order_by('-created_at')[:5]
        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        _sync_premium(perfil)
    else:
        favoritos = []

    onboarding_first_login = request.session.pop('synex_first_login', False)

    return {
        'sidebar_favoritos': favoritos,
        'user_perfil': perfil,
        'onboarding_first_login': onboarding_first_login
    }
