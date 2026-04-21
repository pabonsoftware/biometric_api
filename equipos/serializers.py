from rest_framework import serializers

from .models import (
    EquipoBiomedico,
    Ubicacion,
    Marca,
    Modelo,
    Fabricante,
    TipoTecnologia,
    CodigoQR,
    ArchivoAdjunto
)

class CodigoQRSerializer(serializers.ModelSerializer):

    class Meta: 
        model = CodigoQR

        fields = [
            "id",
            "codigo",
            "fechaGeneracion"
        ]

class ArchivoAdjuntoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArchivoAdjunto

        fields = [
            'id',
            'nombre',
            'archivo',
            'extension',
            'tamano',
            'tipo',
            'ruta',
            'fechaSubida'
        ]

class EquipoBiomedicoSerializer(serializers.ModelSerializer):

    idEquipo = serializers.IntegerField(source="id",read_only=True)

    codigo_qr = CodigoQRSerializer(read_only=True)

    archivos = ArchivoAdjuntoSerializer(
        many=True,
        read_only=True
    )

    marca_nombre = serializers.CharField(source="marca.nombre",read_only=True)
    modelo_nombre = serializers.CharField(source="modelo.nombre",read_only=True)
    fabricante_nombre = serializers.CharField(source="fabricante.nombre",read_only=True)
    tecnologia_nombre = serializers.CharField(source="tipoTecnologia.nombre",read_only=True)
    ubicacion_nombre = serializers.CharField(source="ubicacion.detalle",read_only=True)

    class Meta:

        model = EquipoBiomedico

        fields = '__all__'