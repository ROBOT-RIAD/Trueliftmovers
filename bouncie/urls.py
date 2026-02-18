from django.urls import path
from .views import (
    BouncieAuthorizeView,
    BouncieWebhookView,
    VehicleListView,
    VehicleDetailView,
    VehicleLiveLocationView,
    AllVehiclesLiveLocationView,
    VehicleTripsView,
    VehicleLocationHistoryView,
)

urlpatterns = [
    # OAuth2
    path('authorize/', BouncieAuthorizeView.as_view(), name='bouncie-authorize'),

    # Webhook (Bouncie POSTs here)
    path('webhook/', BouncieWebhookView.as_view(), name='bouncie-webhook'),

    # Vehicles
    path('vehicles/', VehicleListView.as_view(), name='bouncie-vehicles'),
    path('vehicles/location/', AllVehiclesLiveLocationView.as_view(), name='bouncie-all-location'),
    path('vehicles/<str:imei>/', VehicleDetailView.as_view(), name='bouncie-vehicle-detail'),
    path('vehicles/<str:imei>/location/', VehicleLiveLocationView.as_view(), name='bouncie-vehicle-location'),
    path('vehicles/<str:imei>/location/history/', VehicleLocationHistoryView.as_view(), name='bouncie-vehicle-location-history'),
    path('vehicles/<str:imei>/trips/', VehicleTripsView.as_view(), name='bouncie-vehicle-trips'),
]
