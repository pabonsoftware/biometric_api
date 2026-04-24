import qrcode
from io import BytesIO

from django.db import models
from django.core.files import File
from django.conf import settings


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        related_name='modelos'
    )

    class Meta:
        unique_together = ('nombre', 'marca')

    def __str__(self):
        return f"{self.nombre} ({self.marca.nombre})"


class TipoTecnologia(models.TextChoices):
    MONITOREO = 'monitoreo', 'Monitoreo'
    IMAGENOLOGIA = 'imagenologia', 'Imagenología'
    SOPORTE_VITAL = 'soporte_vital', 'Soporte vital'
    DIAGNOSTICO = 'diagnostico', 'Diagnóstico'
    TERAPEUTICO = 'terapeutico', 'Terapéutico'


class EstadoEquipo(models.TextChoices):
    BUENO = 'bueno', 'Bueno'
    REGULAR = 'regular', 'Regular'
    MALO = 'malo', 'Malo'
    DESARMADO = 'desarmado', 'Desarmado'


class Ubicacion(models.Model):

    SEDE_CHOICES = [
        ("pabon", "Clínica Cardiovascular Pabón"),
        ("centro_cuidados", "Centro de Cuidados Cardioneurovascular Pabón")
    ]

    DEPARTAMENTO_CHOICES = [
        ("narino", "Nariño"),
        ("cundinamarca", "Cundinamarca"),
        ("valle", "Valle del Cauca")
    ]

    CIUDAD_CHOICES = [
        ("pasto", "San Juan de Pasto"),
        ("bogota", "Bogotá"),
        ("cali", "Cali")
    ]

    AREA_CHOICES = [
        ("hemodinamia", "Hemodinamia y cirugía cardiovascular"),
        ("hosp_adulto", "Hospitalización adulto"),
        ("uci_6", "UCI 6 piso"),
        ("quirófano", "Quirófano"),
        ("hosp_pediatría", "UCI pedriática"),
        ("uci_coro", "UCI coro"),
        ("hosp_4_adulto", "Hospitalización de 4 piso adulto"),
        ("uci_neo", "UCI neo"),
        ("consulta_prioritaria", "Consulta prioritaria"),
        ("farmacia", "Farmacia"),
        ("imagenología", "Imagenología"),
        ("laboratorio", "Laboratorio clínico")
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


class EquipoBiomedico(models.Model):
    nombre = models.CharField(max_length=100)

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name='equipos'
    )

    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.PROTECT,
        related_name='equipos'
    )

    tipo_tecnologia = models.CharField(
        max_length=20,
        choices=TipoTecnologia.choices
    )

    estado_equipo = models.CharField(
        max_length=20,
        choices=EstadoEquipo.choices,
        default=EstadoEquipo.BUENO
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
        return f"{self.id} - {self.nombre} ({self.marca.nombre})"


class TipoFalla(models.TextChoices):
    DEPRECIACION = 'depreciacion', 'Depreciación'
    MALA_OPERACION = 'mala_operacion', 'Mala operación'
    MAL_INSTALADO = 'mal_instalado', 'Mal instalado'
    ACCESORIOS = 'accesorios', 'Accesorios'
    SIN_FALLAS = 'sin_fallas', 'Sin fallas'


class Falla(models.Model):
    equipo = models.ForeignKey(
        EquipoBiomedico,
        on_delete=models.CASCADE,
        related_name='fallas'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoFalla.choices
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción opcional de la falla"
    )

    fechaRegistro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - Equipo {self.equipo.id}"


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

        qr.save(buffer, format="PNG")

        nombre_archivo = f"equipo_{self.equipo.id}.png"

        self.codigo.save(nombre_archivo, File(buffer), save=False)

    def save(self, *args, **kwargs):

        if not self.codigo:
            self.generarCodigo()

        super().save(*args, **kwargs)

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
