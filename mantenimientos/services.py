from .models import (
    Mantenimiento,
    OrdenServicio,
    ProgramacionMantenimiento,
)

from equipos.models import (
    EquipoBiomedico
)

from notificaciones.models import Notificacion
from services.notifications.notificacion_service import notificar

def crear_mantenimiento(data):

    mantenimiento = Mantenimiento.objects.create(**data)

    mensaje = f"Se ha creado un mantenimiento para el equipo {mantenimiento.equipo.nombre}"

    notificar(
        mantenimiento.responsable,
        "Nuevo mantenimiento asignado",
        mensaje,
        tipo="mantenimiento"
    )

    return mantenimiento

def actualizar_mantenimiento(mantenimiento,data):

    for key,value in data.items():

        setattr(mantenimiento,key,value)

    mantenimiento.save()

    mensaje = f"El mensaje para el equipo {mantenimiento.equipo.nombre} ha sido actualizado"

    notificar(
        mantenimiento.responsable,
        "Mantenimiento actualizado",
        mensaje,
        tipo="mantenimiento"
    )

    return mantenimiento

def supervisar_mantenimiento(mantenimiento):

    mantenimiento.estado = "aprobado"

    mantenimiento.save()

    mensaje = f"El mantenimiento para el equipo {mantenimiento.equipo.nombre} ha sido aprobado."

    notificar(
        mantenimiento.responsable,
        "Mantenimiento aprobado",
        mensaje,
        tipo="mantenimiento"
    )


    programaciones = ProgramacionMantenimiento.objects.filter(
        equipo=mantenimiento.equipo
    )

    return programaciones


def crear_orden_servicio(data):

    orden = OrdenServicio.objects.create(**data)

    mensaje = f"Se ha creado una orden de servicio para el equipo {orden.mantenimiento.equipo.nombre}"

    notificar(
        orden.mantenimiento.responsable,
        "Nueva orden de servicio",
        mensaje,
        tipo="mantenimiento"
    )

    return orden

def generar_reporte_general():

    total_equipos = EquipoBiomedico.objects.count()

    total_mantenimientos = Mantenimiento.objects.count()

    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado="pendiente"
    ).count()

    ordenes_ejecutadas = OrdenServicio.objects.filter(
        estado="ejecutada"
    ).count()

    return {
        "totalEquipos":total_equipos,
        "totalMantenimientos":total_mantenimientos,
        "mantenimientosPendientes":mantenimientos_pendientes,
        "ordenesEjecutadas":ordenes_ejecutadas
    }