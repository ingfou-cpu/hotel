"""
Configuration Django du projet HotelBooking.

Toutes les valeurs sensibles ou dépendantes de l'environnement sont lues
depuis le fichier ``backend/.env`` via django-environ.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173"]),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    BOOKING_TAX_RATE=(float, 0.10),
    BOOKING_SERVICE_FEE=(float, 5.0),
    BOOKING_CANCELLATION_DEADLINE_DAYS=(int, 2),
)

# Lit les variables depuis backend/.env (ignoré si le fichier est absent).
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ---------------------------------------------------------------------------
# Sécurité
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="dev-only-change-me-not-safe")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librairies
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    # Applications métier
    "apps.core",
    "apps.accounts",
    "apps.hotels",
    "apps.bookings",
    "apps.payments",
    "apps.reviews",
    "apps.notifications",
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
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Base de données (PostgreSQL en production, SQLite par défaut en dev)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_USER_MODEL = "accounts.User"

# ---------------------------------------------------------------------------
# Mots de passe
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et médias
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS (frontend React/Vite servi en :5173)
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env("CORS_ALLOW_ALL_ORIGINS")
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Django REST Framework + JWT (SimpleJWT)
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        # Honore `throttle_scope` sur les vues (register/login) avec un bucket
        # "auth" strict ; sans scope, la classe laisse passer les requêtes.
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": "60/minute",
        # Lecture publique du catalogue (hôtels, expériences…) : tolérante aux
        # rechargements/onglets multiples. Les tentatives d'auth restent dans
        # un bucket "auth" plus strict (voir apps/accounts).
        "anon": "120/minute",
        "auth": "30/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------------------------------------------------------------------
# Emails (console en développement, SMTP en production)
# Note : Django 6 gère les emails via MAILERS — EMAIL_BACKEND est déprécié.
# ---------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="noreply@hotelbooking.local"
)
MAILERS = {
    "default": {
        "BACKEND": env(
            "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
        )
    }
}
if MAILERS["default"]["BACKEND"].endswith("smtp.EmailBackend"):
    MAILERS["default"].update(
        {
            "HOST": env("EMAIL_HOST", default=""),
            "PORT": env.int("EMAIL_PORT", default=587),
            "USERNAME": env("EMAIL_HOST_USER", default=""),
            "PASSWORD": env("EMAIL_HOST_PASSWORD", default=""),
            "USE_TLS": env.bool("EMAIL_USE_TLS", default=True),
            "DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
        }
    )

# ---------------------------------------------------------------------------
# Celery + Redis (tâches asynchrones : emails, rappels…)
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
# Exécution synchrone (sans broker) : pratique en dev/tests. Mettre à false en
# prod dès que le worker Celery tourne.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Planification périodique (celery beat) :
# - expirer les paiements en attente trop anciens (chaque nuit à 03h00) ;
# - rappels d'arrivée pour les séjours sous 2 jours (toutes les 30 minutes).
CELERY_BEAT_SCHEDULE = {
    "expire-stale-payments": {
        "task": "apps.payments.tasks.expire_stale_payments",
        "schedule": crontab(hour=3, minute=0),
    },
    "scan-upcoming-reminders": {
        "task": "apps.bookings.tasks.scan_upcoming_reminders",
        "schedule": crontab(minute="*/30"),
    },
}

# Durée avant laquelle un paiement en attente est considéré comme expiré (s).
PAYMENT_PENDING_TIMEOUT_SECONDS = env.int("PAYMENT_PENDING_TIMEOUT_SECONDS", default=3600)

# Nom du site (emails, notifications).
SITE_NAME = env("SITE_NAME", default="HotelBooking")

# ---------------------------------------------------------------------------
# Stripe (utilisé à partir de l'étape « Paiement »)
# ---------------------------------------------------------------------------
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="eur")

# ---------------------------------------------------------------------------
# Règles métier des réservations
# ---------------------------------------------------------------------------
BOOKING_TAX_RATE = env("BOOKING_TAX_RATE")
BOOKING_SERVICE_FEE = env("BOOKING_SERVICE_FEE")
BOOKING_CANCELLATION_DEADLINE_DAYS = env("BOOKING_CANCELLATION_DEADLINE_DAYS")

# URL du frontend (liens dans les emails, redirections Stripe…)
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

# ---------------------------------------------------------------------------
# Documentation API (OpenAPI/Swagger via drf-spectacular)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "HotelBooking API",
    "DESCRIPTION": (
        "API de réservation hôtelière : comptes (JWT), hôtels, chambres, "
        "réservations, paiements Stripe, avis et notifications."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}