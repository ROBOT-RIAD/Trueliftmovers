from django.urls import path
from .views import BouncieAuthorizeView

urlpatterns = [
    # Step 1 – authenticated user requests the Bouncie authorization URL
    path('authorize/', BouncieAuthorizeView.as_view(), name='bouncie-authorize'),
    # /callback/ is registered directly in the root urls.py to match Bouncie portal redirect URI
]
