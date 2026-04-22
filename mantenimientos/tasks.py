from celery import shared_task
from django.core.mail import send_mail
from .models import Mantenimiento,Notificacion
from django.conf import settings
from .email_service import enviar_alerta_correo
from datetime import date 

from .models import ProgramacionMantenimiento


def _es_mantenimiento_vencido(programacion,hoy):
    return programacion.proximoMantenimiento and programacion.proximoMantenimiento <= hoy

def _obtener_ultimo_mantenimiento(equipo):
    return Mantenimiento.objects.filter(equipo=equipo).last()

def _notificacion_existente(mensaje,destinatario):
    return Notificacion.objects.filter(
        mensaje=mensaje,
        estado='pendiente',
        tipo='mantenimiento',
        destinatario=destinatario
    ).exists()

def _crear_notificacion(mensaje,destinatario):
    Notificacion.objects.create(
        mensaje=mensaje,
        estado='pendiente',
        tipo='mantenimiento',
        destinatario=destinatario
    )


def _enviar_correo(destinatario,mensaje):
    enviar_alerta_correo(destinatario,mensaje)


@shared_task
def verificar_mantenimientos_periodicamente():

    hoy = date.today()
    programaciones = ProgramacionMantenimiento.objects.all()

    for programacion in programaciones:
        if _es_mantenimiento_vencido(programacion,hoy):
            mensaje = f"El equipo {programacion.equipo.nombre} requiere mantenimiento"
            mantenimiento = _obtener_ultimo_mantenimiento(programacion.equipo)

            if mantenimiento:
                destinatario = mantenimiento.responsable.correo
                if not _notificacion_existente(mensaje,destinatario):
                    _crear_notificacion(mensaje,destinatario)
                    _enviar_correo(destinatario,mensaje)