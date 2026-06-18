import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CentralManagement.settings")

app = Celery("CentralManagement")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
