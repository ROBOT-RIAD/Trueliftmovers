from django.urls import include, path
from support.views import SupportAPIView
from notifications.views import NotificationListAPIView,NotificationReadUpdateAPIView

urlpatterns = [
   path('support/', SupportAPIView.as_view(), name='support'),
   path('notifications/', NotificationListAPIView.as_view(), name='notifications-list'),
   path('notifications/read/<int:notification_id>/',NotificationReadUpdateAPIView.as_view(),name='notification-read'),
]