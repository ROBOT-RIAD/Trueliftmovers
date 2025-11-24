from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordReserOTP, User
from datetime import timedelta
from django.utils import timezone



@shared_task
def send_otp_email(user_id, otp):
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Your OTP Code",
            message=f"Hello {user.username}, your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        return f"OTP sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"
    



@shared_task
def cleanup_expired_otps():
    expired = PasswordReserOTP.objects.filter(
        is_verified=False,
        created_at__lt=timezone.now() - timedelta(minutes=5)
    )
    count = expired.count()
    expired.delete()
    return f"{count} expired OTPs deleted"


