from django.urls import include, path
from TermdAndPrivacy.views import TermsAPIView,PrivacyAPIView
from truck.views import TruckListCreateView, TruckDetailAPIView
from notifications.views import NotificationListAPIView

urlpatterns = [
   path("terms/", TermsAPIView.as_view(), name="terms"),
   path("privacy/", PrivacyAPIView.as_view(), name="privacy"),

   path('trucks/', TruckListCreateView.as_view(), name='truck-list-create'),
   path('trucks/<int:pk>/', TruckDetailAPIView.as_view(), name='truck-detail'),


   path('notifications/', NotificationListAPIView.as_view(), name='notifications-list'),
]