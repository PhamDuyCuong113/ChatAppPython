from django.contrib import admin
from django.urls import path, include
from chat import views as chat_views
from registration import views as rv
from django.conf import settings
from django.conf.urls.static import static   # 🟢 thêm dòng này

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🏠 Trang chủ
    path('', chat_views.home, name='home'),

    # 🔐 Auth
    path('accounts/', include('django.contrib.auth.urls')),

    # 💬 Chat app
    path('chat/', include('chat.urls')),

    # 👤 Đăng ký tài khoản
    path('signup/', rv.SignUp, name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

