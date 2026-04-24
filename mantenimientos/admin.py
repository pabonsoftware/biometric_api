from django.contrib import admin
from .models import (
    Mantenimiento,
    OrdenServicio,
    ProgramacionMantenimiento,
    CertificadoMetrologico,
    Reporte,
    EstadoMantenimiento,
    CheckListMantenimiento,
    MantenimientoHistorial
)

admin.site.register(Mantenimiento)
admin.site.register(OrdenServicio)
admin.site.register(ProgramacionMantenimiento)
admin.site.register(CertificadoMetrologico)
admin.site.register(Reporte)
admin.site.register(MantenimientoHistorial)
admin.site.register(CheckListMantenimiento)
admin.site.register(EstadoMantenimiento)