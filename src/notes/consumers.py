# notes/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NoteNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # on peut gérer des messages ici plus tard
        pass

    async def send_note_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'note',
            'message': event['message'],
        }))
