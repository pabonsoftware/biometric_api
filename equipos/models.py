import qrcode
from io import BytesIO

from django.db import models
from django.core.files import File


class Ubicacion(models.Model):

    SEDE_CHOICES = [
        ("pabon","Clínica Cardiovascular Pabón"),
        ("centro_cuidados","Centro de Cuidados Cardioneurovascular Pabón")
    ]

    DEPARTAMENTO_CHOICES = [
        ("narino","Nariño"),
        ("cundinamarca","Cundinamarca"),
        ("valle","Valle del Cauca")
    ]

    CIUDAD_CHOICES = [
        ("pasto","San Juan de Pasto"),
        ("bogota","Bogotá"),
        ("cali","Cali")
    ]

    AREA_CHOICES = [
        ("hemodinamia","Hemodinamia y cirugía cardiovascular"),
        ("hosp_adulto","Hospitalización adulto"),
        ("uci_6","UCI 6 piso"),
        ("quirófano","Quirófano"),
        ("hosp_pediatría","UCI pedriática"),
        ("uci_coro","UCI coro"),
        ("hosp_4_adulto","Hospitalización de 4 piso adulto"),
        ("uci_neo","UCI neo"),
        ("consulta_prioritaria","Consulta prioritaria"),
        ("farmacia","Farmacia"),
        ("imagenología","Imagenología"),
        ("laboratorio","Laboratorio clínico")
    ]

    sede = models.CharField(
        max_length=50,
        choices=SEDE_CHOICES
    )

    departamento = models.CharField(
        max_length=50,
        choices=DEPARTAMENTO_CHOICES
    )

    ciudad = models.CharField(
        max_length=50,
        choices=CIUDAD_CHOICES
    )

    area = models.CharField(
        max_length=50,
        choices=AREA_CHOICES
    )

    detalle = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.get_sede_display()} - {self.get_area_display()} - {self.detalle}"
    

class Marca(models.Model):

    MARCA_CHOICES = [
        ("philips","Philips"),
        ("ge","GE Healthcare"),
        ("siemnens","Siemens"),
        ("mindray","Mindray"),
        ("drager","Drager")
    ]

    nombre = models.CharField(
        max_length=50,
        choices=MARCA_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
class Modelo(models.Model):

    MODELO_CHOICES = [
        ("mx800","IntelliVue MX800"),
        ("b450","B450 Monitor"),
        ("acuity","Acuity LT"),
        ("evita_v300","Evita V300"),
        ("resona7","Resona 7")
    ]

    nombre = models.CharField(
        max_length=100,
        choices=MODELO_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
class Fabricante(models.Model):

    FABRICANTE_CHOICES = [
        ("philips","Philips Medical System"),
        ("ge","GE HealthCare"),
        ("siemens","Siemens Healthineers"),
        ("mindray","Mindray Bio-Medical Electronics"),
        ("drager","Dragerwerk AG"),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=FABRICANTE_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    

class TipoTecnologia(models.Model):

    TECNOLOGIA_CHOICES = [
        ("monitoreo","Monitoreo"),
        ("imagenologia","Imagenología"),
        ("soporte_vital","Soporte vital"),
        ("diagnostico","Diagnóstico"),
        ("terapeutico","Terapéutico"),
    ]

    nombre = models.CharField(
        max_length=50,
        choices=TECNOLOGIA_CHOICES
    )

    def __str__(self):
        return self.get_display()
    
