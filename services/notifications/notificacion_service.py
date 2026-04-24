from notificaciones.models import Notificacion
from services.email.tasks import send_email_task

def notificar(usuario,asunto,mensaje,tipo="sistema"):

    if not usuario:

        return 
    
    Notificacion.objects.create(
        usuario=usuario,
        mensaje=mensaje,
        tipo=tipo
    )

    if usuario.correo:
        send_email_task.delay(
            usuario.correo,
            asunto,
            mensaje
        )