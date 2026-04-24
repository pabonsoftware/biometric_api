from rest_framework import serializers

from .models import (
    EquipoBiomedico,
    Marca,
    Modelo,
    Falla,
    CodigoQR,
    ArchivoAdjunto,
    TipoTecnologia,
    EstadoEquipo,
    TipoFalla
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


class MarcaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Marca
        fields = ['id', 'nombre']


class ModeloSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(source='marca.nombre', read_only=True)

    class Meta:
        model = Modelo
        fields = ['id', 'nombre', 'marca', 'marca_nombre']


class FallaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Falla
        fields = ['id', 'equipo', 'tipo', 'tipo_display', 'descripcion', 'fechaRegistro']
        read_only_fields = ['fechaRegistro']


class EquipoBiomedicoSerializer(serializers.ModelSerializer):
    idEquipo = serializers.IntegerField(source="id", read_only=True)

    codigo_qr = CodigoQRSerializer(read_only=True)

    archivos = ArchivoAdjuntoSerializer(
        many=True,
        read_only=True
    )

    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True)
    modelo_nombre = serializers.CharField(source="modelo.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_equipo_display", read_only=True)
    tecnologia_display = serializers.CharField(source="get_tipo_tecnologia_display", read_only=True)

    fallas = FallaSerializer(many=True, read_only=True)

    class Meta:

        model = EquipoBiomedico

        fields = [
            'idEquipo', 'nombre',
            'marca', 'marca_nombre',
            'modelo', 'modelo_nombre',
            'tipo_tecnologia', 'tecnologia_display',
            'estado_equipo', 'estado_display',
            'serie', 'placa',
            'ubicacion',
            'fallas',
            'codigo_qr', 'archivos',
            'fechaRegistro'
        ]


class EquipoBiomedicoWriteSerializer(serializers.ModelSerializer):

    class Meta:

        model = EquipoBiomedico

        fields = [
            'nombre', 'marca', 'modelo',
            'tipo_tecnologia', 'estado_equipo',
            'serie', 'placa', 'ubicacion'
        ]

    def validate(self, data):
        marca = data.get('marca')
        modelo = data.get('modelo')

        if self.instance:
            marca = marca or self.instance.marca
            modelo = modelo or self.instance.modelo

        if marca and modelo:
            if modelo.marca_id != marca.id:
                raise serializers.ValidationError({
                    'modelo': (
                        f"El modelo '{modelo.nombre}' no pertenece a la marca "
                        f"'{marca.nombre}'. Seleccione un modelo de esa marca."
                    )
                })
        return data
