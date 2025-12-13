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


