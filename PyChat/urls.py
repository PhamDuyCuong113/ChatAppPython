from django.contrib import admin
from django.urls import path, include
from chat import views as chat_views
from registration import views as rv
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 Custom login + verify OTP
    path('login/', chat_views.login_view, name='custom_login'),
    path('verify-otp/', chat_views.verify_otp, name='verify_otp'),

    # 🏠 Trang chủ
    path('', chat_views.home, name='home'),

    # 💬 Chat app
    path('chat/', include('chat.urls')),

    # 👤 Đăng ký tài khoản
    path('signup/', rv.SignUp, name='register'),

    # 🔒 Django default auth (đặt cuối để không đè custom login)
    path('accounts/', include('django.contrib.auth.urls')),
]

# 📦 File tĩnh & media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
