import random
from datetime import timedelta
from django.utils import timezone
from accounts.models import OTP

def generate_otp(user, type):
    # Invalidate old unused OTPs
    OTP.objects.filter(user=user, type=type, is_used=False).update(is_used=True)

    otp_code = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=5)

    otp = OTP.objects.create(
        user=user,
        otp_code=otp_code,
        type=type,
        expires_at=expires_at
    )

    return otp_code
