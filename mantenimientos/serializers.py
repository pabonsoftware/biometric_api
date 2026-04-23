from rest_framework import serializers
from .models import (
    Mantenimiento,
    ProgramacionMantenimiento,
    OrdenServicio,
    CertificadoMetrologico,
    Notificacion,
    Reporte
)

from equipos.models import EquipoBiomedico
from usuarios.models import Usuario

class MantenimientoSerializer(serializers.ModelSerializer):

    idMantenimiento = serializers.IntegerField(source="id",read_only=True)

    equipo = serializers.PrimaryKeyRelatedField(
        queryset=EquipoBiomedico.objects.all()
    )

    responsable = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all()
    )

    equipoNombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    responsableNombre = serializers.CharField(
        source="responsable.nombre",
        read_only=True
    )

    class Meta:

        model = Mantenimiento

        fields = '__all__'

class ProgramacionMantenimientoSerializer(serializers.ModelSerializer):

    idProgramacion = serializers.IntegerField(source="id",read_only=True)

    equipo = serializers.PrimaryKeyRelatedField(
        queryset=EquipoBiomedico.objects.all()
    )

    equipoNombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    class Meta:
        model = ProgramacionMantenimiento
        fields = '__all__'

class OrdenServicioSerializer(serializers.ModelSerializer):

    idOrden = serializers.IntegerField(source="id",read_only=True)

    mantenimientoEquipo = serializers.CharField(
        source="mantenimiento.equipo.nombre",
        read_only=True
    )

    class Meta:
        model = OrdenServicio
        fields = '__all__'

class CertificadoMetrologicoSerializer(serializers.ModelSerializer):

    idCertificado = serializers.IntegerField(source="id",read_only=True)

    responsableNombre = serializers.CharField(
        source="responsable.nombre",
        read_only=True
    )

    class Meta:
        model = CertificadoMetrologico
        fields = '__all__'

class NotificacionSerializer(serializers.ModelSerializer):

    idNotificacion = serializers.IntegerField(source="id",read_only=True)

    class Meta:
        model = Notificacion
        fields = '__all__'

class ReporteSerializer(serializers.ModelSerializer):

    idReporte = serializers.IntegerField(source="id",read_only=True)

    equipo = serializers.PrimaryKeyRelatedField(
        source="mantenimiento.equipo.id",
        read_only=True
    )

    equipoNombre = serializers.CharField(
        source="mantenimiento.equipo.id",
        read_only=True
    )

    class Meta:
        model = Reporte
        fields = '__all__'