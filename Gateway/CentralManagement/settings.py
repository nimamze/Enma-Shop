from pathlib import Path
from dotenv import load_dotenv
import os

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
    "storages",
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
    AWS_ACCESS_KEY_ID = os.getenv("ARVAN_S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("ARVAN_S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv(
        "ARVAN_S3_BUCKET_NAME", "enma-shop-accounts-avatars"
    )
    AWS_S3_REGION_NAME = os.getenv("ARVAN_S3_REGION_NAME", "ir-thr-at1")
    AWS_S3_ENDPOINT_URL = os.getenv(
        "ARVAN_S3_ENDPOINT_URL", "https://s3.ir-thr-at1.arvanstorage.ir"
    )
    AWS_S3_CUSTOM_DOMAIN = os.getenv(
        "ARVAN_S3_CUSTOM_DOMAIN",
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.arvanstorage.ir",
    )
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "region_name": AWS_S3_REGION_NAME,
                "endpoint_url": AWS_S3_ENDPOINT_URL,
                "default_acl": AWS_DEFAULT_ACL,
                "querystring_auth": AWS_QUERYSTRING_AUTH,
                "file_overwrite": AWS_S3_FILE_OVERWRITE,
                "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

AUTH_USER_MODEL = "Accounts.User"
