from celery import shared_task
from .email_service import send_mail

@shared_task
def send_email_task(to,subject,message):
    send_mail(to,subject,message)

    