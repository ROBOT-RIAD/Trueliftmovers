from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Support



@shared_task
def send_support_notification(support_id,email):
    try:
        support = Support.objects.get(id=support_id)
        subject = f"New Support Request: {support.title}"
        message = f"User {support.user.profile.full_name} submitted a support request.\n\nText: {support.text}"
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )
        return f"Notification sent for support {support.id}"
    except Support.DoesNotExist:
        return "Support request not found"
    
