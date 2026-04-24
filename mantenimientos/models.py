from django.db import models

from datetime import date,timedelta
from django.utils import timezone

from equipos.models import EquipoBiomedico, ArchivoAdjunto
from usuarios.models import Usuario

class Prioridad(models.TextChoices):
    BAJA = "baja","Baja"
    MEDIA = "media","Media"
    ALTA = "alta","Alta",
    CRITICA = "critica","Crítica"

class EstadoMantenimiento(models.TextChoices):
    PENDIENTE = "pendiente","Pendiente"
    APROBADO = "aprobado","Aprobado"
    EN_PROCESO = "en_proceso","En proceso"
    FINALIZADO = "finalizado","Finalizado"
    ATRASADO = "atrasado","Atrasado"

class Mantenimiento(models.Model):

    equipo = models.ForeignKey("equipos.EquipoBiomedico",on_delete=models.CASCADE)
    responsable = models.ForeignKey("usuarios.Usuario",on_delete=models.CASCADE,null=True)

    descripcion = models.TextField()

    prioridad = models.CharField(
        max_length=20,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoMantenimiento.choices,
        default=EstadoMantenimiento.PENDIENTE
    )

    fecha_programada = models.DateTimeField()
    fecha_inicio = models.DateTimeField(null=True,blank=True)
    fecha_fin = models.DateTimeField(null=True,blank=True)

    fecha_limite = models.DateTimeField()

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now_add=True)

    def esta_atrasado(self):
        return self.fecha_limite < timezone.now() and self.estado != "finalizado"
    
    def __str__(self):
        return f"{self.equipo.nombre} - {self.estado}"
    
class MantenimientoHistorial(models.Model):

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='historial'
    )

    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True
    )

    acccion = models.CharField(max_length=100)

    cambios = models.JSONField(default=dict)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} - {self.fecha}"
    
class EventoMantenimiento(models.Model):

    TIPO_EVENTO = [
        ("creado","Creado"),
        ("actualizado","Actualizado"),
        ("aprobado","Aprobado"),
        ("finalizado","Finalizado")
    ]

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE
    )

    tipo = models.CharField(max_length=50,choices=TIPO_EVENTO)

    descripcion = models.TextField()

    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True
    )

    fecha = models.DateTimeField(auto_now_add=True)

class CheckListMantenimiento(models.Model):

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='checklist'
    )

    item = models.CharField(max_length=255)

    completado = models.BooleanField(default=False)

    fecha = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return self.item
    
class EvidenciaMantenimiento(models.Model):

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='evidencias'
    )

    archivo = models.FileField(upload_to='mantenimientos/')

    descripcion = models.CharField(max_length=255)

    fecha = models.DateTimeField(auto_now_add=True)

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

    ultimaEjecucion = models.DateField(null=True,blank=True)

    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)

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

    def esta_vencido(self):
        return self.proximoMantenimiento and self.proximoMantenimiento < date.today()

    def __str__(self):
        return f"{self.equipo.nombre} - Mant: {self.frecuenciaMantenimiento}"
    

class OrdenServicio(models.Model):

    ESTADO_CHOICES = [
        ('aprobada','APROBADA'),
        ('pendiente','PENDIENTE'),
        ('finalizada','FINALIZADA'),
        ('cancelada','CANCELADA')
    ]

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='ordenes'
    )

    responsable = models.ForeignKey(Usuario,on_delete=models.SET_NULL,null=True)

    tipoServicio = models.CharField(max_length=50)

    fechaInicio = models.DateField(auto_now_add=True)
    fechaFin = models.DateField(null=True,blank=True)

    descripcion = models.TextField()

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES
    )

    duracionHoras = models.IntegerField(
        null=True,
        blank=True
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

    archivo = models.FileField(upload_to='certificados/',null=True,blank=True)

    valido_hasta = models.DateField(null=True,blank=True)

    def __str__(self):
        return f"{self.numeroCertificado} - {self.fecha}"
    
class Reporte(models.Model):

    TIPO_CHOICES = [
        ('correctivo','CORRECTIVO'),
        ('preventivo','PREVENTIVO'),
        ('calibracion','CALIBRACION'),
        ('falla','FALLA'),
    ]

    mantenimiento = models.ForeignKey(
        Mantenimiento,
        on_delete=models.CASCADE,
        related_name='reportes'
    )

    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)

    nombre = models.CharField(max_length=100)

    descripcion = models.TextField(blank=True)

    fechaGeneracion = models.DateTimeField(auto_now_add=True)

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES
    )

    archivo = models.FileField(upload_to='reportes/',null=True,blank=True)

    version = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.nombre} - {self.tipo}"