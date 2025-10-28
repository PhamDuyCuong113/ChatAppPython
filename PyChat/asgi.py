import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# ⚙️ Đặt biến môi trường TRƯỚC khi import chat.routing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PyChat.settings")

import chat.routing  # <-- chuyển xuống đây

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
