from celery import shared_task
from django.utils import timezone
from .models import Truck
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer



@shared_task
def process_bouncie_event(payload):

    if payload.get("eventType") != "tripData":
        return

    imei = str(payload.get("imei")).strip()

    data_points = payload.get("data", [])
    if not data_points:
        return

    latest = data_points[-1]   # last point
    gps = latest.get("gps", {})

    lat = gps.get("lat")
    lon = gps.get("lon")

    updated = Truck.objects.filter(imei=imei).update(
        live_lat=lat,
        live_lon=lon,
        live_speed=latest.get("speed"),
        live_heading=gps.get("heading"),
        last_location_update=timezone.now()
    )