from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Truck
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender=Truck)
def send_truck_update(sender, instance, created, **kwargs):
    if not created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "truck_updates",
            {
                "type": "truck_update",
                "data": {
                    "imei": instance.imei,
                    "truck_number_plate": instance.truck_number_plate,
                    "driver_name": instance.driver_name,
                    "live_lat": instance.live_lat,
                    "live_lon": instance.live_lon,
                    "live_speed": instance.live_speed,
                    "live_heading": instance.live_heading,
                    "last_location_update": str(instance.last_location_update),
                }
            }
        )