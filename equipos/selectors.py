from .models import EquipoBiomedico

def obtener_equipos():

    return EquipoBiomedico.objects.all()


def obtener_equipo_por_id(pk):

    return EquipoBiomedico.objects.get(pk=pk)


def buscar_equipo(nombre=None, serie=None, marca=None, modelo=None, ubicacion=None):

    queryset = EquipoBiomedico.objects.all()

    if nombre:
        queryset = queryset.filter(nombre__icontains=nombre)

    if serie:
        queryset = queryset.filter(serie__icontains=serie)

    if marca:
        queryset = queryset.filter(marca__nombre__icontains=marca)

    if modelo: 
        queryset = queryset.filter(modelo__nombre__icontains=modelo)

    if ubicacion:
        queryset = queryset.filter(ubicacion__id=ubicacion)

    return queryset