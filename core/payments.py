import json
import hmac
import hashlib
import urllib.request
import urllib.error
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Payment, Subscription, Perfil


class AbacatePayError(Exception):
    pass


def _get_setting(name, default=""):
    value = getattr(settings, name, default)
    return value or default


def _api_post(path, payload):
    base_url = _get_setting("ABACATEPAY_API_URL")
    token = _get_setting("ABACATEPAY_TOKEN")
    if not base_url or not token:
        raise AbacatePayError("Abacate Pay is not configured.")

    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise AbacatePayError(f"Abacate Pay HTTP {exc.code}: {body}")

    return json.loads(body) if body else {}


def _is_simulation_enabled():
    return str(_get_setting("ABACATEPAY_SIMULATE_PIX", "false")).lower() == "true"


def _parse_timestamp(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return timezone.datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return timezone.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _mark_premium_for_one_time(user):
    perfil = Perfil.objects.filter(usuario=user).first()
    if not perfil:
        return
    perfil.is_premium = True
    if not perfil.premium_activated_at:
        perfil.premium_activated_at = timezone.now()
    days = int(_get_setting("ABACATEPAY_ONE_TIME_DAYS", 30))
    perfil.premium_expires_at = timezone.now() + timedelta(days=days)
    perfil.save(update_fields=["is_premium", "premium_activated_at", "premium_expires_at"])


def _create_pix_qrcode(user, amount_cents, currency, description):
    path = _get_setting("ABACATEPAY_PIX_QRCODE_PATH", "pixQrCode")
    payload = {
        "amount": amount_cents,
        "description": description,
        "metadata": {"user_id": user.id},
    }
    response = _api_post(path, payload)
    data = response.get("data") if isinstance(response, dict) else {}
    qrcode_id = None
    if isinstance(data, dict):
        qrcode_id = data.get("id") or data.get("pixQrCodeId")
    if not qrcode_id:
        qrcode_id = response.get("id") if isinstance(response, dict) else None
    if not qrcode_id:
        raise AbacatePayError("PIX QRCode id missing in Abacate Pay response.")
    return qrcode_id, response


def _simulate_pix_payment(qrcode_id, metadata=None):
    path = _get_setting("ABACATEPAY_PIX_SIMULATE_PATH", "pixQrCode/simulate-payment")
    payload = {"metadata": metadata or {}}
    response = _api_post(f"{path}?id={qrcode_id}", payload)
    return response


def create_abacate_checkout(user, kind, amount_cents, currency, success_url, cancel_url, description):
    if kind == "one_time":
        if not _is_simulation_enabled():
            raise AbacatePayError("PIX simulation disabled. Set ABACATEPAY_SIMULATE_PIX=true.")
        qrcode_id, response = _create_pix_qrcode(user, amount_cents, currency, description)
        payment = Payment.objects.create(
            usuario=user,
            provider="abacate",
            provider_id=qrcode_id,
            kind=kind,
            status="pending",
            amount_cents=amount_cents,
            currency=currency,
            raw_payload=response,
        )
        simulate_response = _simulate_pix_payment(qrcode_id, metadata={"user_id": user.id})
        payment.status = "paid"
        payment.raw_payload = simulate_response
        payment.save(update_fields=["status", "raw_payload", "updated_at"])
        _mark_premium_for_one_time(user)
        return None

    path = _get_setting("ABACATEPAY_CHECKOUT_PATH", "checkout")
    payload = {
        "mode": "subscription" if kind == "subscription" else "payment",
        "amount": amount_cents,
        "currency": currency,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "description": description,
        "metadata": {"user_id": user.id},
        "customer": {
            "name": user.get_full_name() or user.username,
            "email": user.email,
        },
    }

    response = _api_post(path, payload)

    provider_id = response.get("id") or response.get("payment_id") or response.get("checkout_id") or ""
    checkout_url = response.get("checkout_url") or response.get("url") or response.get("redirect_url") or ""

    subscription = None
    subscription_id = response.get("subscription_id")
    if not subscription_id and isinstance(response.get("subscription"), dict):
        subscription_id = response["subscription"].get("id")

    if kind == "subscription" and subscription_id:
        subscription, _ = Subscription.objects.get_or_create(
            provider="abacate",
            provider_id=subscription_id,
            defaults={
                "usuario": user,
                "status": "created",
                "amount_cents": amount_cents,
                "currency": currency,
                "raw_payload": response,
            },
        )

    Payment.objects.create(
        usuario=user,
        subscription=subscription,
        provider="abacate",
        provider_id=provider_id,
        kind=kind,
        status="created",
        amount_cents=amount_cents,
        currency=currency,
        checkout_url=checkout_url,
        raw_payload=response,
    )

    if not checkout_url:
        raise AbacatePayError("Checkout URL missing in Abacate Pay response.")

    return checkout_url


def cancel_abacate_subscription(subscription):
    path = _get_setting("ABACATEPAY_CANCEL_PATH", "subscriptions/{subscription_id}/cancel")
    if "{subscription_id}" not in path:
        raise AbacatePayError("ABACATEPAY_CANCEL_PATH must include {subscription_id}.")

    _api_post(path.format(subscription_id=subscription.provider_id), {"reason": "user_request"})
    subscription.status = "canceled"
    subscription.save(update_fields=["status", "updated_at"])


def _normalize_status(event, status):
    raw = (status or event or "").lower()
    for key in ["paid", "succeeded", "success", "active"]:
        if key in raw:
            return "paid" if "payment" in raw else "active"
    for key in ["failed", "error", "declined"]:
        if key in raw:
            return "failed"
    for key in ["canceled", "cancelled"]:
        if key in raw:
            return "canceled"
    for key in ["pending", "processing", "created"]:
        if key in raw:
            return "pending"
    if "past_due" in raw or "past-due" in raw:
        return "past_due"
    if "expired" in raw:
        return "expired"
    return raw or "unknown"


def _verify_signature(request):
    secret = _get_setting("ABACATEPAY_WEBHOOK_SECRET")
    if not secret:
        # AVISO (deploy): nunca deixe webhook sem secret em produção.
        return settings.DEBUG

    signature = request.headers.get("X-Abacate-Signature") or request.headers.get("X-Signature")
    if not signature:
        return False

    expected = hmac.new(secret.encode("utf-8"), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def handle_abacate_webhook(request):
    if not _verify_signature(request):
        return False, "invalid signature"

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return False, "invalid payload"

    event = payload.get("event") or payload.get("type") or ""
    data = payload.get("data") or {}
    metadata = data.get("metadata") or payload.get("metadata") or {}

    user_id = metadata.get("user_id") or metadata.get("userId")
    provider_payment_id = data.get("payment_id") or data.get("id") or data.get("checkout_id")
    provider_subscription_id = data.get("subscription_id")
    if not provider_subscription_id and isinstance(data.get("subscription"), dict):
        provider_subscription_id = data["subscription"].get("id")

    status = _normalize_status(event, data.get("status"))
    amount = data.get("amount") or data.get("amount_cents") or 0
    currency = data.get("currency") or _get_setting("ABACATEPAY_CURRENCY", "BRL")

    subscription = None
    if provider_subscription_id:
        subscription = Subscription.objects.filter(provider="abacate", provider_id=provider_subscription_id).first()
        if not subscription and user_id:
            subscription = Subscription.objects.create(
                usuario_id=user_id,
                provider="abacate",
                provider_id=provider_subscription_id,
                amount_cents=amount,
                currency=currency,
                status=status,
                raw_payload=payload,
            )
        if subscription:
            subscription.status = status
            subscription.raw_payload = payload
            period_end = _parse_timestamp(data.get("current_period_end") or data.get("period_end"))
            if period_end:
                subscription.current_period_end = period_end
            subscription.save(update_fields=["status", "raw_payload", "current_period_end", "updated_at"])

    payment = None
    if provider_payment_id:
        payment = Payment.objects.filter(provider="abacate", provider_id=provider_payment_id).first()
    if not payment and user_id:
        payment = Payment.objects.filter(usuario_id=user_id, provider="abacate").order_by("-created_at").first()

    if payment:
        payment.status = status
        payment.raw_payload = payload
        if amount:
            payment.amount_cents = amount
        if currency:
            payment.currency = currency
        payment.save(update_fields=["status", "raw_payload", "amount_cents", "currency", "updated_at"])

    perfil = None
    if user_id:
        perfil = Perfil.objects.filter(usuario_id=user_id).first()
    if not perfil and payment:
        perfil = Perfil.objects.filter(usuario=payment.usuario).first()
    if not perfil and subscription:
        perfil = Perfil.objects.filter(usuario=subscription.usuario).first()

    if perfil:
        if status in ["paid", "active"]:
            perfil.is_premium = True
            if not perfil.premium_activated_at:
                perfil.premium_activated_at = timezone.now()

            if subscription and subscription.current_period_end:
                perfil.premium_expires_at = subscription.current_period_end
            elif payment and payment.kind == "one_time":
                days = int(_get_setting("ABACATEPAY_ONE_TIME_DAYS", 30))
                perfil.premium_expires_at = timezone.now() + timedelta(days=days)

            perfil.save(update_fields=["is_premium", "premium_activated_at", "premium_expires_at"])

        if status in ["canceled", "failed", "past_due", "expired"] and subscription:
            if subscription.current_period_end and subscription.current_period_end > timezone.now():
                perfil.is_premium = True
                perfil.premium_expires_at = subscription.current_period_end
            else:
                perfil.is_premium = False
                perfil.premium_activated_at = None
                perfil.premium_expires_at = None
            perfil.save(update_fields=["is_premium", "premium_activated_at", "premium_expires_at"])

    return True, "ok"
