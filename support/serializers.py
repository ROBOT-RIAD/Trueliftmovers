from rest_framework import serializers
from .models import Support
from .tasks import send_support_notification,send_support_realtime_notification
from notifications.tasks import create_notification_task



class SupportSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    text = serializers.CharField()


    def validate_title(self, value):
        if len(value) < 2:
            raise serializers.ValidationError({"title": "Title must be at least 2 characters long."})
        return value
    

    def save(self, **kwargs):
        user = self.context['request'].user
        support = Support.objects.create(
            user=user,
            title=self.validated_data['title'],
            text=self.validated_data['text'],
            resolved=self.validated_data.get('resolved', False)
        )

        create_notification_task.delay(
        user_id=user.id,
        title="Support Request Submitted",
        body=f"Your support request '{support.title}' has been received.",
        data={
            "id": support.id,
            "user": support.user.id,
            "full_name": support.user.profile.full_name,
            "image": support.user.profile.image.url if support.user.profile.image else None,
            "title": support.title,
            "text": support.text,
            "resolved": support.resolved,
            "created_at": str(support.created_at),
        }
        )

        send_support_notification.delay(support.id)

        # send_support_realtime_notification.delay(
        #     user_id=user.id,
        #     support_id=support.id,
        #     title="Support Request Submitted",
        #     body=f"You submitted a support request: {support.title}",
        #     data={
        #         "id": support.id,
        #         "title": support.title,
        #         "text": support.text,
        #         "resolved": support.resolved,
        #         "created_at": str(support.created_at),
        #         "user_id": user.id,
        #         "full_name": getattr(user.profile, "full_name", user.username),
        #         "image": user.profile.image.url if getattr(user, "profile", None) and getattr(user.profile, "image", None) else None
        #     },
        #     event_type="support_created",
        #     broadcast_admin=True
        # )
        return support