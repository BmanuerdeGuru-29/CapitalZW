from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_notification_task(user_email, title, message):
    """
    Asynchronously send an email notification.
    """
    send_mail(
        subject=f"[CapitalZW] {title}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True,
    )
