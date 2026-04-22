from .models import (
    Mantenimiento,
    OrdenServicio,
    ProgramacionMantenimiento,
)

from equipos.models import (
    EquipoBiomedico
)

from .tasks import (
    _notificacion_existente,
    _crear_notificacion,
    _enviar_correo
)

def crear_mantenimiento(data):

    mantenimiento = Mantenimiento.objects.create(**data)

    mensaje = f"Se ha creado un mantenimiento para el equipo {mantenimiento.equipo.nombre}"

    destinatario = mantenimiento.responsable.correo

    if not _notificacion_existente(mensaje,destinatario):
        _crear_notificacion(mensaje,destinatario)
        _enviar_correo(destinatario,mensaje)

    return mantenimiento


def actualizar_mantenimiento(mantenimiento,data):

    for key,value in data.items():
        setattr(mantenimiento,key,value)

    mantenimiento.save()

    mensaje = f"El mantenimiento del equipo {mantenimiento.equipo.nombre} ha sido actualizado"

    destinatario = mantenimiento.responsable.pygame.sprite.collide_rect_ratio()

    if not _notificacion_existente(mensaje,destinatario):
        _crear_notificacion(mensaje,destinatario)
        _enviar_correo(destinatario,mensaje)

    return mantenimiento

def eliminar_mantenimiento(mantenimiento):

    equipo = mantenimiento.equipo
    responsable = mantenimiento.responsable

    mensaje = f"El mantenimiento para el equipo {equipo.nombre} ha sido eliminado"

    if not _notificacion_existente(mensaje,responsable.correo):
        _crear_notificacion(mensaje,responsable.correo)
        _enviar_correo(responsable.correo,mensaje)

def supervisar_mantenimiento(mantenimiento):

    mantenimiento.estado = "aprobado"

    mantenimiento.save()

    mensaje = f"El mantenimiento para el equipo {mantenimiento.equipo.nombre} ha sido aprobado."

    if not _notificacion_existente(mensaje,mantenimiento.responsable.correo):
        _crear_notificacion(mensaje,mantenimiento.responsable.correo)
        _enviar_correo(mantenimiento.responsable.correo, mensaje)


    programaciones = ProgramacionMantenimiento.objects.filter(
        equipo=mantenimiento.equipo
    )

    return programaciones


def crear_orden_servicio(data):

    orden = OrdenServicio.objects.create(**data)

    mensaje = f"Se ha creado una nueva orden de servicio para el equipo {orden.mantenimiento.equipo}."
    if not _notificacion_existente(mensaje,orden.mantenimiento.responsable.correo):
        _crear_notificacion(mensaje,orden.mantenimiento.responsable.correo)
        _enviar_correo(orden.mantenimiento.responsable.correo,mensaje)

    return orden

def generar_reporte_general():

    total_equipos = EquipoBiomedico.objects.count()

    total_mantenimientos = Mantenimiento.objects.count()

    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado="pendiente"
    ).count()

    ordenes_ejecutadas = OrdenServicio.objects.filter(
        estado="ejecutado"
    ).count()

    return {
        "totalEquipos":total_equipos,
        "totalMantenimientos":total_mantenimientos,
        "mantenimientosPendientes":mantenimientos_pendientes,
        "ordenesEjecutadas":ordenes_ejecutadas
    }