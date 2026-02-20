import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from truck.models import Truck
from channels.db import database_sync_to_async
import asyncio
from booking.models import Booking



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user is None or user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        if user.role == "admin":
            await self.channel_layer.group_add("admin_notifications", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if self.scope["user"].role == "admin":
            await self.channel_layer.group_discard("admin_notifications", self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))




class TruckLocationConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_user_trucks(self, user):
        if user.is_staff:
            return list(Truck.objects.filter(imei__isnull=False))
        else:
            bookings = Booking.objects.filter(user=user, status="start").select_related("truck")
            trucks = [b.truck for b in bookings if b.truck and b.truck.imei]
            return trucks

    async def connect(self):
        await self.channel_layer.group_add("truck_updates", self.channel_name)
        await self.accept()

        user = self.scope["user"]
        trucks = await self.get_user_trucks(user)

        for truck in trucks:
            await self.send(text_data=json.dumps({
                "imei": truck.imei,
                "truck_number_plate": truck.truck_number_plate,
                "driver_name": truck.driver_name,
                "live_lat": truck.live_lat,
                "live_lon": truck.live_lon,
                "live_speed": truck.live_speed,
                "live_heading": truck.live_heading,
                "last_location_update": str(truck.last_location_update),
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("truck_updates", self.channel_name)

    async def truck_update(self, event):
        user = self.scope["user"]
        truck_imei = event["data"]["imei"]

        if not truck_imei:
            return

        trucks = await self.get_user_trucks(user)
        if any(truck.imei == truck_imei for truck in trucks):
            await self.send(text_data=json.dumps(event["data"]))

