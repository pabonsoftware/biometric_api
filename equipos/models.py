import qrcode
from io import BytesIO

from django.db import models
from django.core.files import File
from django.conf import settings


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
        return self.get_nombre_display()
    
class Estado(models.Model):

    estado = models.JSONField(
        blank=True,
        null=True
    )

class TipoMantenimiento(models.Model):

    tipo_mantenimiento = models.JSONField(
        blank=True,
        null=True
    )

    
class EquipoBiomedico(models.Model):

    nombre = models.CharField(max_length=100)

    fallas = models.JSONField(
        blank=True,
        null=True
    )

    tipo_mantenimiento = models.JSONField(
        TipoMantenimiento,
        null=True
    )

    estado_equipo = models.JSONField(
        Estado,
        null=True
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True
    )

    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True
    )

    fabricante = models.ForeignKey(
        Fabricante,
        on_delete=models.SET_NULL,
        null=True
    )

    tipoTecnologia = models.ForeignKey(
        TipoTecnologia,
        on_delete=models.SET_NULL,
        null=True
    )

    serie = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número de serie del equipo biomédico"
    )

    placa = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text='Número de inventario interno del hospital'
    )

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.CASCADE
    )

    fechaRegistro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.nombre}"
    
class CodigoQR(models.Model):

    equipo = models.OneToOneField(
        EquipoBiomedico,
        on_delete=models.CASCADE,
        related_name='codigo_qr'
    )

    codigo = models.ImageField(upload_to='qr_equipos/')

    fechaGeneracion = models.DateField(auto_now_add=True)

    def generarCodigo(self):

        url = f"{settings.BASE_URL}/api/equipos/{self.equipo.id}/"

        qr = qrcode.make(url)

        buffer = BytesIO()

        qr.save(buffer,format="PNG")

        nombre_archivo = f"equipo_{self.equipo.id}.png"

        self.codigo.save(nombre_archivo,File(buffer),save=False)

    
    def save(self,*args,**kwargs):

        if not self.codigo:
            self.generarCodigo()

        super().save(*args,**kwargs)

    def __str__(self):

        return f"QR Equipo {self.equipo.id}"
    

class ArchivoAdjunto(models.Model):

    equipo = models.ForeignKey(
        EquipoBiomedico,
        on_delete=models.CASCADE,
        related_name='archivos'
    )

    nombre = models.CharField(max_length=100)

    archivo = models.FileField(upload_to='archivos_adjuntos/')

    extension = models.CharField(max_length=20)

    tamano = models.IntegerField()

    tipo = models.CharField(max_length=80)

    ruta = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    fechaSubida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre