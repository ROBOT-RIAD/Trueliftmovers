from rest_framework import serializers
from .models import Notification
from accounts.models import User


class NotificationUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    phone = serializers.CharField(source="profile.phone", read_only=True)
    image = serializers.ImageField(source="profile.image", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "image"]




class NotificationSerializer(serializers.ModelSerializer):
    user = NotificationUserSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ['id','user','title','body','data','read','created_at']
