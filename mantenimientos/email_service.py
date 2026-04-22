from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def enviar_alerta_correo(destinatario,mensaje):

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST:
        logger.warning(
            "Email not sent to %s: SMTP credentials are not configured.",destinatario
        )
        return 
    
    try:
        send_mail(
             "Alerta de mantenimiento biomédico",
            mensaje,
            settings.EMAIL_HOST_USER,
            [destinatario],
            fail_silently=False,
        )

    except Exception as e:
        logger.error("Failed to send email to %s: %s", destinatario, e)