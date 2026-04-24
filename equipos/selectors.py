from .models import EquipoBiomedico, Marca, Modelo, Falla, Ubicacion
from django.shortcuts import get_object_or_404


def obtener_equipos():
    return EquipoBiomedico.objects.select_related('marca', 'modelo', 'ubicacion').all()


def obtener_equipo_por_id(pk):
    return get_object_or_404(EquipoBiomedico, pk=pk)


def obtener_marcas():
    return Marca.objects.all().order_by('nombre')


def obtener_marca_por_id(pk):
    return Marca.objects.get(pk=pk)


def obtener_modelos():
    return Modelo.objects.select_related('marca').all().order_by('marca__nombre', 'nombre')


def obtener_modelos_por_marca(marca_id):
    return Modelo.objects.filter(marca_id=marca_id).order_by('nombre')


def obtener_modelo_por_id(pk):
    return Modelo.objects.get(pk=pk)


def obtener_fallas_por_equipo(equipo_id):
    return Falla.objects.filter(equipo_id=equipo_id).order_by('-fechaRegistro')


def obtener_ubicaciones():
    return Ubicacion.objects.all().order_by('sede', 'area')


def obtener_ubicacion_por_id(pk):
    return Ubicacion.objects.get(pk=pk)
