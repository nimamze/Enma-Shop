from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, email_address, message):
    try:
        send_mail(
            "Enma Shop",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_address],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms(self, phone, message):
    try:
        params = {
            "sender": "2000660110",
            "receptor": f"{phone}",
            "message": f"{message}",
        }
        settings.SMS_API.sms_send(params)

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def send_inactive_users_reminder_task():
    cutoff = timezone.now() - timedelta(days=30)
    message = "It has been a month since you last visited Enma Shop. We miss you."
    users = (
        User.objects.filter(last_login__isnull=False, last_login__lte=cutoff)
        .exclude(email__isnull=True)
        .exclude(email="")
    )
    sent_count = 0
    for user in users.iterator():
        send_email_task.delay(user.email, message)  # type: ignore
        sent_count += 1
    return sent_count


@shared_task
def cleanup_expired_jwt_tokens():
    call_command("flushexpiredtokens")
