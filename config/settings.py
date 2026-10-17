"""
Yangi Samarqand — backend settings.

All environment-specific values come from environment variables (or a local `.env` file),
so the same settings module serves development and production.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------- core

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

if not DEBUG and SECRET_KEY.startswith("dev-only"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # local
    "apps.core",
    "apps.accounts",
    "apps.content",
    "apps.projects",
    "apps.council",
    "apps.forum",
    "apps.partners",
    "apps.inbox",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------- database

if os.environ.get("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --------------------------------------------------------------------------- auth

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------- i18n

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Samarkand"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- static & media

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
SERVE_MEDIA = env_bool("DJANGO_SERVE_MEDIA", False)  # Docker: Next.js image optimizer reads /media via Django

DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIZE_MB = 10
MAX_DOCUMENT_SIZE_MB = 25
MAX_VIDEO_SIZE_MB = 500

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- security
# The Next.js frontend proxies /api and /media to Django, so the browser talks to a single
# origin and Django's session + CSRF protection work unchanged.

FRONTEND_ORIGINS = env_list("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CSRF_TRUSTED_ORIGINS = FRONTEND_ORIGINS
CORS_ALLOWED_ORIGINS = FRONTEND_ORIGINS
CORS_ALLOW_CREDENTIALS = True

# Production runs behind HTTPS (https://mentadbirkor.uz, nginx terminates TLS). Only a plain-HTTP test setup
# needs DJANGO_HTTPS=false — otherwise browsers drop the Secure session and CSRF cookies and nobody can sign in.
# No SSL redirect here: Next.js and the bot call Django over the internal Docker network (http://backend:8000).
HTTPS = env_bool("DJANGO_HTTPS", not DEBUG)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 hours
SESSION_COOKIE_SECURE = HTTPS
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = HTTPS
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if HTTPS:
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# --------------------------------------------------------------------------- REST framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["apps.core.permissions.IsStaffOrReadOnly"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "public_forms": "20/hour",
        "login": "10/min",
        "telegram_code": "8/min",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Yangi Samarqand API",
    "DESCRIPTION": "Samarqand viloyati tadbirkorlari jamoat maslahat kengashi — sayt va admin panel API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --------------------------------------------------------------------------- frontend cache revalidation
# When content changes, Django pings Next.js so cached public pages refresh immediately.

NEXT_REVALIDATE_URL = os.environ.get("NEXT_REVALIDATE_URL", "http://127.0.0.1:3000/internal/revalidate")
NEXT_REVALIDATE_SECRET = os.environ.get("NEXT_REVALIDATE_SECRET", "dev-revalidate-secret")

# --------------------------------------------------------------------------- Telegram login
# Visitors register by sharing their phone with the bot and sign in with the one-time code it sends.
# The bot is a separate aiogram project (../samarkand_bot) that owns the Telegram token and calls
# /api/bot/* with this shared secret (same value in both .env files).

BOT_API_SECRET = os.environ.get("BOT_API_SECRET", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "").lstrip("@")  # fallback; the bot reports it
TELEGRAM_LOGIN_CODE_TTL = int(os.environ.get("TELEGRAM_LOGIN_CODE_TTL", "300"))  # seconds
TELEGRAM_CODE_COOLDOWN = int(os.environ.get("TELEGRAM_CODE_COOLDOWN", "30"))  # seconds between two codes
SITE_USER_SESSION_AGE = 60 * 60 * 24 * 30  # visitors stay signed in for 30 days

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.server": {"level": "WARNING"}},
}
