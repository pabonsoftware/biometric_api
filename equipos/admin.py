from django.contrib import admin
from .models import (
    Marca, Modelo, EquipoBiomedico, Falla,
    Ubicacion, CodigoQR, ArchivoAdjunto
)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    search_fields = ['nombre']


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'marca']
    list_filter = ['marca']
    search_fields = ['nombre', 'marca__nombre']


@admin.register(EquipoBiomedico)
class EquipoBiomedicoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'marca', 'modelo', 'tipo_tecnologia', 'estado_equipo', 'serie']
    list_filter = ['tipo_tecnologia', 'estado_equipo', 'marca']
    search_fields = ['nombre', 'serie', 'placa']
    raw_id_fields = ['marca', 'modelo', 'ubicacion']


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'sede', 'departamento', 'ciudad', 'area']
    list_filter = ['sede', 'departamento', 'ciudad', 'area']
    search_fields = ['detalle']


@admin.register(Falla)
class FallaAdmin(admin.ModelAdmin):
    list_display = ['id', 'equipo', 'tipo', 'fechaRegistro']
    list_filter = ['tipo']
    search_fields = ['equipo__nombre', 'descripcion']


admin.site.register(CodigoQR)
admin.site.register(ArchivoAdjunto)