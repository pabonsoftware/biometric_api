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

    class Meta:

        fields = [
            "idEquipo",
            "nombre",
            "marca",
            "modelo",
            "fabricante",
            "tipoTecnologia",
            "serie",
            "ubicacion",
            "fechaRegistro",
            "codigo_qr",
            "archivos"
        ]