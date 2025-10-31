# PyChat/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# ⚙️ Đặt biến môi trường trước khi load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PyChat.settings")

# ✅ Import routing sau khi set môi trường
import chat.routing


# ==============================
# ASGI application cho Django + Channels
# ==============================
application = ProtocolTypeRouter({
    # HTTP (phục vụ trang web bình thường)
    "http": get_asgi_application(),

    # WebSocket (chat realtime)
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
