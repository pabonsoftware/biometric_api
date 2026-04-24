from django.db import models

from datetime import date,timedelta

from equipos.models import EquipoBiomedico
from usuarios.models import Usuario

class Mantenimiento(models.Model):

    ESTADO_CHOICES = [
        ('pendiente','PENDIENTE'),
        ('en_proceso','EN PROCESO'),
        ('completado','COMPLETADO'),
        ('aprobado','APROBADO'),
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

    diagnostico = models.TextField(
        help_text="Descripción del diagnóstico del mantenimiento",
        blank=False
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        default='mantenimiento'
    )

    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de inicio del mantenimiento"
    )

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de finalización del mantenimiento"
    )

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"

    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError

        if not self.diagnostico or not self.diagnostico.strip():
            raise ValidationError({'diagnostico': 'El diagnóstico no puede estar vacío.'})

        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({
                'fecha_fin': 'La fecha de finalización debe ser mayor o igual a la fecha de inicio.'
            })

    def __str__(self):
        return f"{self.equipo.nombre} - {self.get_estado_display()}"
    
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

    frecuencia_mantenimiento = models.IntegerField()

    frecuencia_calibracion = models.IntegerField()

    unidad_frecuencia = models.CharField(
        max_length=10,
        choices=UNIDAD_FRECUENCIA
    )

    proximo_mantenimiento = models.DateField(blank=True, null=True)

    proximo_calibracion = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Programación de Mantenimiento"
        verbose_name_plural = "Programaciones de Mantenimiento"

    def calcular_proxima_fecha(self):
        """Calcula la próxima fecha de mantenimiento y calibración"""
        hoy = date.today()

        if self.unidad_frecuencia == "dias":
            proximo_mantenimiento = hoy + timedelta(days=self.frecuencia_mantenimiento)
            proximo_calibracion = hoy + timedelta(days=self.frecuencia_calibracion)

        elif self.unidad_frecuencia == "meses":
            proximo_mantenimiento = hoy + timedelta(days=30 * self.frecuencia_mantenimiento)
            proximo_calibracion = hoy + timedelta(days=30 * self.frecuencia_calibracion)

        elif self.unidad_frecuencia == "anios":
            proximo_mantenimiento = hoy + timedelta(days=365 * self.frecuencia_mantenimiento)
            proximo_calibracion = hoy + timedelta(days=365 * self.frecuencia_calibracion)

        else:
            raise ValueError("Unidad de Frecuencia no válida")

        self.proximo_mantenimiento = proximo_mantenimiento
        self.proximo_calibracion = proximo_calibracion

        self.save()

    def __str__(self):
        return f"{self.equipo.nombre} - Mant: {self.frecuencia_mantenimiento}"
    

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

    tipo_servicio = models.CharField(max_length=50)

    fecha_inicio = models.DateField(auto_now_add=True)

    fecha_fin = models.DateField(null=True, blank=True)

    descripcion = models.TextField()

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"

    def __str__(self):
        return f"Orden {self.id} - {self.mantenimiento.equipo.nombre}"
    
class CertificadoMetrologico(models.Model):

    numero_certificado = models.IntegerField()

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Certificado Metrológico"
        verbose_name_plural = "Certificados Metrológicos"
        unique_together = ('numero_certificado',)

    def __str__(self):
        return f"{self.numero_certificado} - {self.fecha}"
    
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

    fecha_generacion = models.DateTimeField(auto_now_add=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"{self.tipo} - {self.estado}"