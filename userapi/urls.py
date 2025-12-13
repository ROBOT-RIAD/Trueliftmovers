from django.urls import include, path
from support.views import SupportAPIView

urlpatterns = [
   path('support/', SupportAPIView.as_view(), name='support'),
]