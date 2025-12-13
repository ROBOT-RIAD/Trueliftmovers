from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Support
from notifications.utils import send_realtime_notification


@shared_task
def send_support_notification(support_id):
    try:
        support = Support.objects.get(id=support_id)
        subject = f"New Support Request: {support.title}"
        message = f"User {support.user.profile.full_name} submitted a support request.\n\nText: {support.text}"
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
        )
        return f"Notification sent for support {support.id}"
    except Support.DoesNotExist:
        return "Support request not found"
    


@shared_task
def send_support_realtime_notification(user_id,support_id,title,body,data,event_type="support_created",broadcast_admin=True):
    send_realtime_notification(user_id=user_id,title=title,body=body,data=data,event_type=event_type,broadcast_admin=broadcast_admin)
    return f"Realtime support notification sent for support {support_id}"