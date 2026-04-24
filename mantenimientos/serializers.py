"""
Serializers for maintenance operations.

Implements input validation and output formatting for maintenance CRUD operations.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from .models import (
    Mantenimiento,
    ProgramacionMantenimiento,
    OrdenServicio,
    CertificadoMetrologico,
    Reporte
)

from equipos.models import EquipoBiomedico
from usuarios.models import Usuario


class MantenimientoCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new maintenance record.

    Validates:
    - equipo_id: must exist
    - diagnostico: cannot be empty
    - fecha_inicio: must be provided
    - responsable_id: must exist
    - tipo: must be a valid type choice
    """

    equipo_id = serializers.IntegerField(required=True)
    diagnostico = serializers.CharField(required=True, min_length=1)
    fecha_inicio = serializers.DateTimeField(required=True)
    responsable_id = serializers.IntegerField(required=True)
    tipo = serializers.ChoiceField(
        choices=[choice[0] for choice in Mantenimiento.TIPO_CHOICES],
        default='preventivo'
    )
    fecha_fin = serializers.DateTimeField(required=False, allow_null=True)

    def validate_equipo_id(self, value):
        """Validate that equipment exists."""
        if not EquipoBiomedico.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Equipo con ID {value} no existe.")
        return value

    def validate_responsable_id(self, value):
        """Validate that responsible user exists."""
        if not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Usuario con ID {value} no existe.")
        return value

    def validate_diagnostico(self, value):
        """Validate that diagnosis is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("El diagnóstico no puede estar vacío.")
        return value.strip()

    def validate(self, data):
        """Validate date consistency."""
        if data.get('fecha_fin') and data.get('fecha_inicio'):
            if data['fecha_fin'] < data['fecha_inicio']:
                raise serializers.ValidationError(
                    "La fecha de finalización no puede ser anterior a la fecha de inicio."
                )
        return data


class MantenimientoUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating maintenance records.

    Allows updating:
    - diagnostico
    - fecha_inicio
    - fecha_fin
    - responsable_id
    - tipo
    - aprobado_por_id
    """

    diagnostico = serializers.CharField(required=False, min_length=1)
    fecha_inicio = serializers.DateTimeField(required=False)
    fecha_fin = serializers.DateTimeField(required=False, allow_null=True)
    responsable_id = serializers.IntegerField(required=False)
    tipo = serializers.ChoiceField(
        choices=[choice[0] for choice in Mantenimiento.TIPO_CHOICES],
        required=False
    )
    aprobado_por_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_responsable_id(self, value):
        """Validate that responsible user exists."""
        if value and not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Usuario con ID {value} no existe.")
        return value

    def validate_aprobado_por_id(self, value):
        """Validate that approver exists."""
        if value and not Usuario.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Usuario con ID {value} no existe.")
        return value

    def validate_diagnostico(self, value):
        """Validate that diagnosis is not empty."""
        if value and not value.strip():
            raise serializers.ValidationError("El diagnóstico no puede estar vacío.")
        return value.strip() if value else value

    def validate(self, data):
        """Validate date consistency."""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')

        if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
            raise serializers.ValidationError(
                "La fecha de finalización no puede ser anterior a la fecha de inicio."
            )
        return data


class MantenimientoSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and retrieving maintenance records.

    Includes all fields with read-only related fields for equipment, responsible user,
    and approver.
    """

    idMantenimiento = serializers.IntegerField(source="id", read_only=True)

    equipo_id = serializers.IntegerField(read_only=True)
    equipo_nombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    responsable_id = serializers.IntegerField(read_only=True)
    responsable_nombre = serializers.CharField(
        source="responsable.nombre",
        read_only=True
    )

    aprobado_por_id = serializers.IntegerField(read_only=True, allow_null=True)
    aprobado_por_nombre = serializers.SerializerMethodField()

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True
    )
    tipo_display = serializers.CharField(
        source="get_tipo_display",
        read_only=True
    )

    class Meta:
        model = Mantenimiento
        fields = [
            'idMantenimiento',
            'equipo_id',
            'equipo_nombre',
            'diagnostico',
            'estado',
            'estado_display',
            'tipo',
            'tipo_display',
            'fecha_inicio',
            'fecha_fin',
            'responsable_id',
            'responsable_nombre',
            'aprobado_por_id',
            'aprobado_por_nombre',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'idMantenimiento',
            'equipo_id',
            'equipo_nombre',
            'responsable_id',
            'responsable_nombre',
            'aprobado_por_id',
            'aprobado_por_nombre',
            'estado_display',
            'tipo_display',
            'created_at',
            'updated_at'
        ]

    def get_aprobado_por_nombre(self, obj):
        """Get approver name if exists."""
        if obj.aprobado_por:
            return obj.aprobado_por.nombre
        return None


class ProgramacionMantenimientoSerializer(serializers.ModelSerializer):
    """Serializer for maintenance scheduling."""

    idProgramacion = serializers.IntegerField(source="id", read_only=True)

    equipo_id = serializers.IntegerField()
    equipo_nombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    class Meta:
        model = ProgramacionMantenimiento
        fields = [
            'idProgramacion',
            'equipo_id',
            'equipo_nombre',
            'frecuencia_mantenimiento',
            'frecuencia_calibracion',
            'unidad_frecuencia',
            'proximo_mantenimiento',
            'proximo_calibracion',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['idProgramacion', 'proximo_mantenimiento', 'proximo_calibracion']


class OrdenServicioSerializer(serializers.ModelSerializer):
    """Serializer for service orders."""

    idOrden = serializers.IntegerField(source="id", read_only=True)

    mantenimiento_id = serializers.IntegerField(read_only=True)
    mantenimiento_equipo = serializers.CharField(
        source="mantenimiento.equipo.nombre",
        read_only=True
    )

    estado_display = serializers.CharField(
        source="get_estado_display",
        read_only=True
    )

    class Meta:
        model = OrdenServicio
        fields = [
            'idOrden',
            'mantenimiento_id',
            'mantenimiento_equipo',
            'tipo_servicio',
            'fecha_inicio',
            'fecha_fin',
            'descripcion',
            'estado',
            'estado_display',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'idOrden',
            'mantenimiento_id',
            'mantenimiento_equipo',
            'fecha_inicio',
            'estado_display',
            'created_at',
            'updated_at'
        ]

class OrdenServicioWriteSerializer(serializers.ModelSerializer):

    class Meta:

        model = OrdenServicio

        fields = [
            "mantenimiento",
            "tipoServicio",
            "descripcion",
            "estado"
        ]

class CertificadoMetrologicoSerializer(serializers.ModelSerializer):

    idCertificado = serializers.IntegerField(source="id",read_only=True)

    responsableNombre = serializers.CharField(
        source="responsable.nombre",
        read_only=True
    )

    class Meta:
        model = CertificadoMetrologico
        fields = '__all__'


class ReporteSerializer(serializers.ModelSerializer):

    idReporte = serializers.IntegerField(source="id",read_only=True)

    equipoNombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    vencido = serializers.SerializerMethodField()

    def get_vencido(self,obj):
        return obj.esta_vencido

    class Meta:
        model = Reporte
        fields = '__all__'

class ReporteWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reporte
        fields = [
            "mantenimiento",
            "nombre",
            "descripcion",
            "tipo",
            "archivo"
        ]