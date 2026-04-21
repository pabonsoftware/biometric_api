from .models import EquipoBiomedico

def crear_equipo(data):

    equipo = EquipoBiomedico.objects.create(**data)

    return equipo

def actualizar_equipo(equipo,data):

    for key,value in data.items():
        setattr(equipo,key,value)


    equipo.save()

    return equipo

def eliminar_equipo(equipo):

    equipo.delete()