from celery import shared_task
from django.utils import timezone
from .models import Truck

@shared_task
def process_bouncie_event(payload):

    if payload.get("eventType") != "tripData":
        return

    imei = payload.get("imei")

    stats = payload.get("stats", {})
    location = stats.get("location", {})

    lat = location.get("lat")
    lon = location.get("lon")

    Truck.objects.filter(imei=imei).update(
        live_lat=lat,
        live_lon=lon,
        live_speed=stats.get("speed"),
        live_heading=location.get("heading"),
        live_fuel=stats.get("fuelLevel"),
        last_location_update=timezone.now()
    )
