from django.urls import include, path
from TermdAndPrivacy.views import TermsAPIView,PrivacyAPIView

urlpatterns = [
   path("terms/", TermsAPIView.as_view(), name="terms"),
   path("privacy/", PrivacyAPIView.as_view(), name="privacy"),
]