from .models import (
    Mantenimiento,
    ProgramacionMantenimiento,
    OrdenServicio,
    Reporte,
)

def obtener_mantenimientos():

    return Mantenimiento.objects.select_related("equipo","responsable")

def obtener_mantenimiento_por_id(pk):

    return Mantenimiento.objects.select_related(
        "equipo",
        "responsable"
    ).get(pk=pk)

def obtener_programaciones():

    return ProgramacionMantenimiento.objects.select_related(
        "equipo"
    )

def obtener_ordenes():

    return OrdenServicio.objects.select_related(
        "mantenimiento",
        "mantenimiento__equipo"
    )

def obtener_reportes():

    return Reporte.objects.select_related(
        "equipo",
    )

def obtener_reporte_por_id(pk):

    return Reporte.objects.select_related(
        "equipo"
    ).get(pk=pk)

def contar_reportes():

    return Reporte.objects.count()

