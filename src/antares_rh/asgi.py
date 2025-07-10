"""
ASGI config for antares_rh project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

import notes.routing 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'antares_rh.settings')

application = get_asgi_application()
# antares_rh/asgi.py

django.setup()

application = ProtocolTypeRouter({
    "http": application,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(notes.routing.websocket_urlpatterns))
    ),
})
