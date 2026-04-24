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


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'estado', 'tipo', 'responsable', 'created_at')
    list_filter = ('estado', 'tipo', 'created_at')
    search_fields = ('equipo__nombre', 'diagnostico', 'responsable__nombre')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('equipo', 'responsable', 'aprobado_por')
        }),
        ('Detalles', {
            'fields': ('tipo', 'diagnostico', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'mantenimiento', 'tipo_servicio', 'estado', 'fecha_inicio')
    list_filter = ('estado', 'fecha_inicio', 'created_at')
    search_fields = ('mantenimiento__equipo__nombre', 'descripcion', 'tipo_servicio')
    readonly_fields = ('fecha_inicio', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('mantenimiento', 'tipo_servicio', 'estado')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'fecha_inicio', 'fecha_fin')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProgramacionMantenimiento)
class ProgramacionMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'frecuencia_mantenimiento', 'unidad_frecuencia', 'proximo_mantenimiento')
    list_filter = ('unidad_frecuencia', 'created_at')
    search_fields = ('equipo__nombre',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Equipo', {
            'fields': ('equipo',)
        }),
        ('Frecuencias', {
            'fields': ('frecuencia_mantenimiento', 'frecuencia_calibracion', 'unidad_frecuencia')
        }),
        ('Próximas Fechas', {
            'fields': ('proximo_mantenimiento', 'proximo_calibracion')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CertificadoMetrologico)
class CertificadoMetrologicoAdmin(admin.ModelAdmin):
    list_display = ('numero_certificado', 'fecha', 'responsable', 'mantenimiento')
    list_filter = ('fecha', 'created_at')
    search_fields = ('numero_certificado', 'responsable__nombre', 'mantenimiento__equipo__nombre')
    readonly_fields = ('fecha', 'created_at', 'updated_at')
    fieldsets = (
        ('Certificado', {
            'fields': ('numero_certificado', 'fecha', 'responsable')
        }),
        ('Relación', {
            'fields': ('mantenimiento',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'mantenimiento', 'fecha_generacion')
    list_filter = ('tipo', 'fecha_generacion', 'created_at')
    search_fields = ('nombre', 'descripcion', 'mantenimiento__equipo__nombre')
    readonly_fields = ('fecha_generacion', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'mantenimiento')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'falla', 'archivo')
        }),
        ('Auditoría', {
            'fields': ('fecha_generacion', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'estado', 'destinatario', 'fecha')
    list_filter = ('tipo', 'estado', 'fecha', 'created_at')
    search_fields = ('mensaje', 'destinatario', 'tipo')
    readonly_fields = ('fecha', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('tipo', 'estado', 'mensaje')
        }),
        ('Destinatario', {
            'fields': ('destinatario',)
        }),
        ('Auditoría', {
            'fields': ('fecha', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
