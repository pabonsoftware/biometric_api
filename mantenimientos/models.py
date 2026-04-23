from django.db import models

from datetime import date,timedelta

from equipos.models import EquipoBiomedico
from usuarios.models import Usuario

class Mantenimiento(models.Model):

    ESTADO_CHOICES = [
        ('aprobado','APROBADO'),
        ('pendiente','PENDIENTE'),
        ('supervisado','SUPERVISADO'),
        ('ejecutado','EJECUTADO')
    ]

    TIPO_CHOICES = [
        ('preventivo','PREVENTIVO'),
        ('correctivo','CORRECTIVO'),
        ('calibracion','CALIBRACION'),
        ('falla','FALLA'),
        ('sistema','SISTEMA')
    ]

    equipo = models.ForeignKey(
        EquipoBiomedico,
        on_delete=models.CASCADE,
        related_name='mantenimientos'
    )

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        default='mantenimiento'
    )

    fechaInicio = models.DateField(null=True,blank=True)

    fechaFin = models.DateField(null=True,blank=True)

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mantenimientos_responsable'
    )

    aprobado_por = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mantenimientos_aprobados'
    )

    def __str__(self):
        return f"{self.equipo.nombre} - {self.estado}"
    
class ProgramacionMantenimiento(models.Model):

    UNIDAD_FRECUENCIA = [
        ('dias','DIAS'),
        ('meses','MESES'),
        ('anios','AÑOS')
    ]

    equipo = models.ForeignKey(
        EquipoBiomedico,
        on_delete=models.CASCADE,
        related_name='programaciones'
    )

    frecuenciaMantenimiento = models.IntegerField()

    frecuenciaCalibracion = models.IntegerField()

    unidadFrecuencia = models.CharField(
        max_length=10,
        choices=UNIDAD_FRECUENCIA
    )

    proximoMantenimiento = models.DateField(blank=True,null=True)

    proximoCalibracion = models.DateField(blank=True,null=True)

    def calcularProximaFecha(self):

        hoy = date.today()

        if self.unidadFrecuencia == "dias":
            proximo_mantenimiento = hoy + timedelta(days=self.frecuenciaMantenimiento)
            proximo_calibracion = hoy + timedelta(days=self.frecuenciaCalibracion)

        elif self.unidadFrecuencia == "meses":
            proximo_mantenimiento = hoy + timedelta(days=30 * self.frecuenciaMantenimiento)
            proximo_calibracion = hoy + timedelta(days= 30* self.frecuenciaCalibracion)

        elif self.unidadFrecuencia == "anios":
            proximo_mantenimiento = hoy + timedelta(days=365 * self.frecuenciaMantenimiento)
            proximo_calibracion = hoy + timedelta(days=365*self.frecuenciaCalibracion)

        else:
            raise ValueError("Unidad de Freucuencia no válida")
        
        self.proximoMantenimiento = proximo_mantenimiento
        self.proximoCalibracion = proximo_calibracion

        self.save()

    def __str__(self):
        return f"{self.equipo.nombre} - Mant: {self.frecuenciaMantenimiento}"
    

class OrdenServicio(models.Model):

    ESTADO_CHOICES = [
        ('aprobada','APROBADA'),
        ('pendiente','PENDIENTE'),
        ('supervisada','SUPERVISADA'),
        ('ejecutada','EJECUTADA')
    ]

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='ordenes'
    )

    tipoServicio = models.CharField(max_length=50)

    fechaInicio = models.DateField(auto_now_add=True)

    fechaFin = models.DateField(auto_now_add=True)

    descripcion = models.TextField()

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES
    )

    def __str__(self):

        return f"Orden {self.id} - {self.mantenimiento.equipo.nombre}"
    
class CertificadoMetrologico(models.Model):

    numeroCertificado = models.IntegerField()

    fecha = models.DateField(auto_now_add=True)

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='certificados',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.numeroCertificado} - {self.fecha}"
    
class Reporte(models.Model):

    TIPO_CHOICES = [
        ('correctivo','CORRECTIVO'),
        ('preventivo','PREVENTIVO'),
        ('calibracion','CALIBRACION'),
        ('falla','FALLA'),
        ('sistema','SISTEMA')
    ]

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='reportes'
    )

    nombre = models.CharField(max_length=100)

    descripcion = models.TextField(blank=True)

    fechaGeneracion = models.DateTimeField(auto_now_add=True)

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES
    )

    falla = models.JSONField(
        null=True,
        blank=True
    )

    archivo = models.FileField(
        upload_to='reportes/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.nombre} - {self.tipo}"
    
class Notificacion(models.Model):

    ESTADO_CHOICES = [
        ('aprobado','APROBADO'),
        ('pendiente','PENDIENTE'),
        ('supervisado','SUPERVISADO'),
        ('ejecutado','EJECUTADO')
    ]

    TIPO_CHOICES = [
        ('mantenimiento','MANTENIMIENTO'),
        ('calibracion','CALIBRACION'),
        ('falla','FALLA'),
        ('sistema','SISTEMA')
    ]

    mensaje = models.CharField(max_length=200)

    fecha = models.DateField(auto_now_add=True)

    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES
    )

    tipo = models.CharField(
        max_length=35,
        choices=TIPO_CHOICES
    )

    destinatario = models.EmailField()

    def __str__(self):
        return f"{self.tipo} - {self.estado}"