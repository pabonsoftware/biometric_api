from celery import shared_task
from datetime import date 
from .models import ProgramacionMantenimiento,Mantenimiento
from services.notifications.notificacion_service import notificar

def es_mantenimiento_vencido(programacion):
    return (
        programacion.proximoMantenimiento
        and programacion.proximoMantenimiento <= date.today()
    )

def obtener_ultimo_mantenimiento(equipo):
    return Mantenimiento.objects.filter(equipo=equipo).last()

@shared_task
def verificar_mantenimiento():
    programaciones = ProgramacionMantenimiento.objects.select_related("equipo")

    for programacion in programaciones:
        if es_mantenimiento_vencido(programacion):
            
            mantenimiento = obtener_ultimo_mantenimiento(programacion.equipo)

            if mantenimiento:

                mensaje = f"El equipo {programacion.equipo.nombre} requiere mantenimiento"
    
                notificar(
                    mantenimiento.responsable,
                    "Mantenimiento pendiente",
                    mensaje,
                    tipo="mantenimiento "
                ) 