from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('X-Frame-Options', 'DENY')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        )
        if request.is_secure() and not settings.DEBUG:
            response.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "MAINTENANCE_MODE", False):
            return self.get_response(request)

        path = request.path
        maintenance_path = reverse("manutencao")

        allowed_prefixes = ("/static/", "/media/", "/admin/")
        if path == maintenance_path or path.startswith(allowed_prefixes):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user and (user.is_staff or user.is_superuser):
            return self.get_response(request)

        return redirect(maintenance_path)
