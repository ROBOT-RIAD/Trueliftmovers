from celery import shared_task
from notifications.models import Notification
from accounts.models import User
from .utils import send_realtime_notification

@shared_task
def create_notification_task(user_id, title, body, data=None):
    try:
        user = User.objects.get(id=user_id)
        
        notification = Notification.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {}
        )

        send_realtime_notification(user_id, title, body, data,event_type="notification",broadcast_admin=True)

        return f"Notification created and pushed for user {user_id}"

    except User.DoesNotExist:
        return "User not found"
