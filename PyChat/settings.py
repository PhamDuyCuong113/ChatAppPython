"""
Django settings for PyChat project (phiên bản không dùng .env)
"""

import os
import sys
from cryptography.fernet import Fernet
from pymongo import MongoClient

# ==================== BASE DIR ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==================== SECURITY ====================
SECRET_KEY = 'usnm_pu9ng2xf4@q#aens^n4t)_1)b6icnc^1u-f_jko++*=(#'
DEBUG = True
ALLOWED_HOSTS = ['*']  # Cho phép local + LAN

# ==================== APPS ====================
INSTALLED_APPS = [
    # Django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Ứng dụng chính
    'chat',
    'registration.apps.RegistrationConfig',

    # Thư viện ngoài
    'crispy_forms',
    'crispy_bootstrap4',
    'rest_framework',
    'widget_tweaks',

    # Channels (WebSocket)
    'channels',

    # OTP / 2FA
    'django_otp',
    'django_otp.plugins.otp_totp',
    'two_factor',
]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'PyChat.urls'

# ==================== TEMPLATES ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==================== WSGI / ASGI ====================
WSGI_APPLICATION = 'PyChat.wsgi.application'
ASGI_APPLICATION = 'PyChat.asgi.application'

# ==================== DATABASE ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# ==================== AUTH ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== LANGUAGE / TIME ====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==================== STATIC & MEDIA FILES ====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CRISPY_TEMPLATE_PACK = 'bootstrap4'
LOGIN_REDIRECT_URL = "/chat/"
LOGOUT_REDIRECT_URL = "/"

# ==================== CHANNELS (WebSocket) ====================
ASGI_APPLICATION = "PyChat.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}

# ==================== CSRF & SESSION SECURITY ====================
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# ==================== LOGGING ====================
print(">>> USING DATABASE:", DATABASES['default']['NAME'], file=sys.stderr)

# ==================== ENCRYPTION (Fernet) ====================
ENCRYPTION_KEY = b'ImgxRnmTZWbRNiw9Corx53P2sxR9e7wibXUVj8xTl9g='
FERNET = Fernet(ENCRYPTION_KEY)

# ==================== MONGODB ====================
MONGO_URL = "mongodb+srv://phamduycuong:admin123@cuoicung.m45c2wq.mongodb.net/?appName=Cuoicung"
try:
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client["Test"]  # Tên database
    mongo_messages = mongo_db["messages"]
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# ==================== EMAIL (Gửi OTP) ====================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "phamduycuong2005241@gmail.com"      # Gmail thật
EMAIL_HOST_PASSWORD = "gxscfatqdhwkjlgi"               # App password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
