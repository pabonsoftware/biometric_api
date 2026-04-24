from .models import EquipoBiomedico, Marca, Modelo, Falla


def crear_equipo(data):
    equipo = EquipoBiomedico.objects.create(**data)
    return equipo


def actualizar_equipo(equipo, data):
    for key, value in data.items():
        setattr(equipo, key, value)
    equipo.save()
    return equipo


def eliminar_equipo(equipo):
    equipo.delete()


def crear_marca(data):
    return Marca.objects.create(**data)


def actualizar_marca(marca, data):
    for key, value in data.items():
        setattr(marca, key, value)
    marca.save()
    return marca


def eliminar_marca(marca):
    marca.delete()


def crear_modelo(data):
    return Modelo.objects.create(**data)


def actualizar_modelo(modelo, data):
    for key, value in data.items():
        setattr(modelo, key, value)
    modelo.save()
    return modelo


def eliminar_modelo(modelo):
    modelo.delete()


def crear_falla(data):
    return Falla.objects.create(**data)


def eliminar_falla(falla):
    falla.delete()
