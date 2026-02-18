import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection



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


class VehicleLocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time vehicle location/event updates.
    Connect via:  ws/vehicle/{imei}/
    Authentication: JWT token in query param ?token= or Sec-WebSocket-Protocol header.
    """

    async def connect(self):
        self.imei = self.scope["url_route"]["kwargs"]["imei"]
        self.group_name = f"vehicle_{self.imei}"
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close()
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def vehicle_location(self, event):
        """Handles real-time GPS points from tripData webhook events."""
        await self.send(text_data=json.dumps({"type": "location", "data": event["data"]}))

    async def vehicle_event(self, event):
        """Handles tripStart, tripEnd, deviceConnect, and other event types."""
        await self.send(text_data=json.dumps({"type": "event", "data": event["data"]}))


