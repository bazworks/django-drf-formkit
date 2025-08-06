import random
import string

from django.db import models
from django.utils import timezone


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_otp(cls, email: str) -> str:
        """Generate a new OTP for the given email"""
        # Delete any existing unused OTPs for this email
        cls.objects.filter(email=email, is_used=False).delete()

        # Generate a new 6-digit OTP
        otp = "".join(random.choices(string.digits, k=6))

        # Create new OTP record
        cls.objects.create(
            email=email,
            otp=otp,
            expires_at=timezone.now() + timezone.timedelta(minutes=15),
        )

        return otp

    @classmethod
    def validate_otp(cls, email: str, otp: str) -> bool:
        """Validate the OTP for the given email"""
        try:
            otp_obj = cls.objects.get(
                email=email, otp=otp, is_used=False, expires_at__gt=timezone.now()
            )
            otp_obj.is_used = True
            otp_obj.save()
            return True
        except cls.DoesNotExist:
            return False
