from .models import EquipoBiomedico

def obtener_equipos():

    return EquipoBiomedico.objects.all()


def obtener_equipo_por_id(pk):

    return EquipoBiomedico.objects.get(pk=pk)

