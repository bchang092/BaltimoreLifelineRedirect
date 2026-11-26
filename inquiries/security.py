"""Private, database-backed rate limiting for LumaReach inquiries."""

from datetime import datetime, timezone as dt_timezone
from ipaddress import ip_address

from django.conf import settings
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import InquiryRateLimit


def client_ip(request):
    address = request.META.get("REMOTE_ADDR", "")
    if settings.INQUIRY_TRUST_HEROKU_PROXY:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            address = forwarded.split(",")[-1].strip()
    try:
        return str(ip_address(address))
    except ValueError:
        return "unknown"


def reserve_submission_attempt(request, namespace="luma-inquiry-rate"):
    """Atomically count attempts across workers. Return seconds to retry or 0."""
    now = timezone.now()
    window = int(now.timestamp()) // 3600
    expires_at = datetime.fromtimestamp((window + 1) * 3600, dt_timezone.utc)
    key = salted_hmac(
        namespace, f"{client_ip(request)}:{window}", algorithm="sha256"
    ).hexdigest()
    InquiryRateLimit.objects.filter(expires_at__lte=now).delete()
    InquiryRateLimit.objects.get_or_create(key=key, defaults={"expires_at": expires_at})
    accepted = InquiryRateLimit.objects.filter(
        key=key, attempts__lt=settings.INQUIRY_RATE_LIMIT
    ).update(attempts=F("attempts") + 1)
    return 0 if accepted else max(1, int((expires_at - now).total_seconds()) + 1)

