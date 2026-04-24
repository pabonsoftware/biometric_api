from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import ProtectedError

from .models import EquipoBiomedico, Marca, Modelo, Ubicacion, Falla
from .serializers import (
    EquipoBiomedicoSerializer,
    EquipoBiomedicoWriteSerializer,
    MarcaSerializer,
    ModeloSerializer,
    UbicacionSerializer,
    FallaSerializer,
    ArchivoAdjuntoSerializer,
    CodigoQRSerializer
)
from .filters import EquipoFilter
from .selectors import (
    obtener_equipos,
    obtener_equipo_por_id,
    obtener_marcas,
    obtener_marca_por_id,
    obtener_modelos,
    obtener_modelos_por_marca,
    obtener_modelo_por_id,
    obtener_ubicaciones,
    obtener_ubicacion_por_id,
    obtener_fallas_por_equipo,
)
from .services import (
    crear_equipo,
    actualizar_equipo,
    eliminar_equipo,
    crear_marca,
    actualizar_marca,
    eliminar_marca,
    crear_modelo,
    actualizar_modelo,
    eliminar_modelo,
    crear_ubicacion,
    actualizar_ubicacion,
    eliminar_ubicacion,
    crear_falla,
    eliminar_falla,
)
from .models import CodigoQR, ArchivoAdjunto


class MarcaViewSet(viewsets.ModelViewSet):
    serializer_class = MarcaSerializer

    def get_queryset(self):
        return obtener_marcas()

    def create(self, request):
        serializer = MarcaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        marca = crear_marca(serializer.validated_data)
        return Response(MarcaSerializer(marca).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        marca = obtener_marca_por_id(pk)
        serializer = MarcaSerializer(marca, data=request.data)
        serializer.is_valid(raise_exception=True)
        marca = actualizar_marca(marca, serializer.validated_data)
        return Response(MarcaSerializer(marca).data)

    def destroy(self, request, pk=None):
        marca = obtener_marca_por_id(pk)
        try:
            eliminar_marca(marca)
        except ProtectedError:
            return Response(
                {"error": "No se puede eliminar esta marca porque tiene equipos asociados."},
                status=status.HTTP_409_CONFLICT
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModeloViewSet(viewsets.ModelViewSet):
    serializer_class = ModeloSerializer

    def get_queryset(self):
        marca_id = self.request.query_params.get('marca')
        if marca_id:
            return obtener_modelos_por_marca(marca_id)
        return obtener_modelos()

    def create(self, request):
        serializer = ModeloSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        modelo = crear_modelo(serializer.validated_data)
        return Response(ModeloSerializer(modelo).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        modelo = obtener_modelo_por_id(pk)
        serializer = ModeloSerializer(modelo, data=request.data)
        serializer.is_valid(raise_exception=True)
        modelo = actualizar_modelo(modelo, serializer.validated_data)
        return Response(ModeloSerializer(modelo).data)

    def destroy(self, request, pk=None):
        modelo = obtener_modelo_por_id(pk)
        try:
            eliminar_modelo(modelo)
        except ProtectedError:
            return Response(
                {"error": "No se puede eliminar este modelo porque tiene equipos asociados."},
                status=status.HTTP_409_CONFLICT
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class UbicacionViewSet(viewsets.ModelViewSet):
    serializer_class = UbicacionSerializer

    def get_queryset(self):
        return obtener_ubicaciones()

    def create(self, request):
        serializer = UbicacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ubicacion = crear_ubicacion(serializer.validated_data)
        return Response(UbicacionSerializer(ubicacion).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        ubicacion = obtener_ubicacion_por_id(pk)
        serializer = UbicacionSerializer(ubicacion, data=request.data)
        serializer.is_valid(raise_exception=True)
        ubicacion = actualizar_ubicacion(ubicacion, serializer.validated_data)
        return Response(UbicacionSerializer(ubicacion).data)

    def destroy(self, request, pk=None):
        ubicacion = obtener_ubicacion_por_id(pk)
        try:
            eliminar_ubicacion(ubicacion)
        except ProtectedError:
            return Response(
                {"error": "No se puede eliminar esta ubicación porque tiene equipos asociados."},
                status=status.HTTP_409_CONFLICT
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FallaViewSet(viewsets.ModelViewSet):
    serializer_class = FallaSerializer

    def get_queryset(self):
        equipo_id = self.request.query_params.get('equipo')
        if equipo_id:
            return obtener_fallas_por_equipo(equipo_id)
        return Falla.objects.all()

    def create(self, request):
        serializer = FallaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        falla = crear_falla(serializer.validated_data)
        return Response(FallaSerializer(falla).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        falla = Falla.objects.get(pk=pk)
        eliminar_falla(falla)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EquipoBiomedicoViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = EquipoFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return EquipoBiomedicoWriteSerializer
        return EquipoBiomedicoSerializer

    def list(self, request):
        equipos = obtener_equipos()
        serializer = EquipoBiomedicoSerializer(equipos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        serializer = EquipoBiomedicoSerializer(equipo)
        return Response(serializer.data)

    def create(self, request):
        serializer = EquipoBiomedicoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        equipo = crear_equipo(serializer.validated_data)
        return Response(EquipoBiomedicoSerializer(equipo).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        serializer = EquipoBiomedicoWriteSerializer(equipo, data=request.data)
        serializer.is_valid(raise_exception=True)
        equipo = actualizar_equipo(equipo, serializer.validated_data)
        return Response(EquipoBiomedicoSerializer(equipo).data)

    def destroy(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        eliminar_equipo(equipo)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def generar_qr(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        qr, creado = CodigoQR.objects.get_or_create(equipo=equipo)
        qr.save()
        return Response({
            "message": "QR generado correctamente",
            "equipo": equipo.id,
            "qr": qr.codigo.url
        })

    @action(detail=True, methods=["get"])
    def qr(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        qr = equipo.codigo_qr
        return Response({
            "equipo": equipo.id,
            "nombre": equipo.nombre,
            "qr": qr.codigo.url,
            "fechaGeneracion": qr.fechaGeneracion
        })

    @action(detail=True, methods=["post"])
    def adjuntar_archivo(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        serializer = ArchivoAdjuntoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(equipo=equipo)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=["get"])
    def archivos(self, request, pk=None):
        equipo = obtener_equipo_por_id(pk)
        archivos = equipo.archivos.all()
        serializer = ArchivoAdjuntoSerializer(
            archivos,
            many=True
        )
        return Response(serializer.data)
