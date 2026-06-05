from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab
import os
from datetime import timedelta
from kavenegar import KavenegarAPI

BASE_DIR = Path(__file__).resolve().parent.parent  # -> Enma-Shop\Gateway

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = "django-insecure-o(4r##ru5y@mz+!z842##!6-p*x2u93cob$mrfgefz2*)%pu=8"

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "Core.apps.CoreConfig",
    "Accounts.apps.AccountsConfig",
    "Addresses.apps.AddressesConfig",
    "storages",
    "django_celery_beat",
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework",
    "drf_yasg",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "CentralManagement.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR],
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

WSGI_APPLICATION = "CentralManagement.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATA_BASE_NAME"),
        "USER": os.getenv("DATA_BASE_USER_NAME"),
        "PASSWORD": os.getenv("DATA_BASE_PASSWORD"),
        "HOST": os.getenv("DATA_BASE_HOST"),
        "PORT": "5432",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "Accounts.utils.password_validators.MaximumLengthValidator",
        "OPTIONS": {
            "max_length": 10,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    custom_domain = os.getenv(
        "ARVAN_S3_CUSTOM_DOMAIN",
        f"{os.getenv('ARVAN_S3_BUCKET_NAME')}.s3.{'ir-thr-at1'}.arvanstorage.ir",
    )
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": os.getenv("ARVAN_S3_ACCESS_KEY_ID"),
                "secret_key": os.getenv("ARVAN_S3_SECRET_ACCESS_KEY"),
                "bucket_name": os.getenv("ARVAN_S3_BUCKET_NAME"),
                "region_name": "ir-thr-at1",
                "endpoint_url": "https://s3.ir-thr-at1.arvanstorage.ir",
                "default_acl": None,
                "querystring_auth": False,
                "file_overwrite": False,
                "custom_domain": custom_domain,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = f"https://{custom_domain}/"

AUTH_USER_MODEL = "Accounts.User"


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,
                "retry_on_timeout": True,
            },
        },
    }
}


CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_RESULT_EXPIRES = 86400
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "send-inactive-users-reminder-every-friday": {
        "task": "Core.tasks.send_inactive_users_reminder_task",
        "schedule": crontab(minute=0, hour=3, day_of_week=5),
    },
    "cleanup-expired-jwt-tokens-every-night": {
        "task": "Core.tasks.cleanup_expired_jwt_tokens",
        "schedule": crontab(hour=2, minute=0),
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "Accounts.utils.authentication.RedisBlacklistJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "50/day", "user": "100/day"},
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer <token>'",
        },
    }
}
SMS_API = KavenegarAPI(os.getenv("KAVENEGAR_API_KEY"))

MAP_API_KEY = os.getenv("MAP_API_KEY")
MAP_REVERSE_URL = "https://map.ir/reverse"

USER_CHANGE_PASSWORD_TIME_LIMIT = os.getenv("USER_CHANGE_PASSWORD_TIME_LIMIT")
USER_CHANGE_PASSWORD_LIMIT = os.getenv("USER_CHANGE_PASSWORD_LIMIT")
USER_SELLER_TIME_LIMIT = os.getenv("USER_SELLER_TIME_LIMIT")
USER_SELLER_LIMIT = os.getenv("USER_SELLER_LIMIT")
USER_OTP_CODE_LIMIT_TIME = os.getenv("USER_OTP_CODE_LIMIT_TIME")
USER_OTP_CODE_LIMIT = os.getenv("USER_OTP_CODE_LIMIT")
USER_OTP_CODE_TIME = os.getenv("USER_OTP_CODE_TIME")
