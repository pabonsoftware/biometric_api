from rest_framework import serializers
from .models import (
    Mantenimiento,
    ProgramacionMantenimiento,
    OrdenServicio,
    CertificadoMetrologico,
    Reporte
)

from equipos.models import EquipoBiomedico
from usuarios.models import Usuario

class MantenimientoSerializer(serializers.ModelSerializer):

    idMantenimiento = serializers.IntegerField(source="id",read_only=True)

    equipoNombre = serializers.CharField(
        source="equipo.nombre",
        read_only=True
    )

    responsableNombre = serializers.CharField(
        source="responsable.nombre",
        read_only=True
    )

    atrasado = serializers.SerializerMethodField()

    def get_atrasado(self,obj):
        return obj.esta_atrasado()

    class Meta:

        model = Mantenimiento

        fields = '__all__'


class MantenimientoWriteSerializer(serializers.ModelSerializer):

    class Meta:

        model = Mantenimiento

        fields = [
            "equipo",
            "responsable",
            "tipo",
            "descripcion",
            "estado"
        ]

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