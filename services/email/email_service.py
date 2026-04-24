from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def enviar_alerta_correo(to,subject,message):

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST:
        logger.warning(
            f"Email not sent to {to}: SMTP not configured"
        )
        return 
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [to],
            fail_silently=False
        )

    except Exception as e:
        logger.error(f"Error sending email to {to}: {str(e)}")