# notes/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/notifications/", consumers.NoteNotificationConsumer.as_asgi()),
]
