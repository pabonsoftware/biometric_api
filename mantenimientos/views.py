from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action


from .serializers import (
    MantenimientoSerializer,
    CertificadoMetrologicoSerializer,
    NotificacionSerializer,
    OrdenServicioSerializer,
    ProgramacionMantenimientoSerializer,
    ReporteSerializer
)

from .selectors import (
    obtener_mantenimientos,
    obtener_mantenimiento_por_id,
    obtener_ordenes,
    obtener_programaciones,
    obtener_reportes,
    obtener_reporte_por_id,
    obtener_notificaciones
)

from .services import (
    crear_mantenimiento,
    actualizar_mantenimiento,
    supervisar_mantenimiento,
    generar_reporte_general
)

from .models import (
    CertificadoMetrologico,
    ProgramacionMantenimiento,
    OrdenServicio
)

from .filters import (
    MantenimientoFilter,
    ReporteFilter
)

class MantenimientoViewSet(viewsets.ModelViewSet):

    serializer_class = MantenimientoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = MantenimientoFilter

    def get_queryset(self):

        return obtener_mantenimientos()
    
    def retrieve(self,request,pk=None):

        mantenimiento = obtener_mantenimiento_por_id(pk)

        serializer = self.get_serializer(mantenimiento)

        return Response(serializer.data)
    

    def create(self,request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        mantenimiento = crear_mantenimiento(serializer.validated_data)

        return Response(
            MantenimientoSerializer(mantenimiento).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self,request,pk=None):

        mantenimiento = obtener_mantenimiento_por_id(pk)

        serializer = self.get_serializer(
            mantenimiento,
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        actualizar_mantenimiento(
            mantenimiento,
            serializer.validated_data
        )

        return Response(serializer.data)
    
    @action(detail=True,methods=["get"])
    def supervisar(self,request,pk=None):

        mantenimiento = obtener_mantenimiento_por_id(pk)

        programaciones = supervisar_mantenimiento(mantenimiento)

        serializer = ProgramacionMantenimientoSerializer(programaciones,many=True)

        return Response({
            "message":"Mantenimiento supervisado correctamente",
            "data":serializer.data
        })
    
    @action(detail=True,methods=["patch"])
    def aprobar(self,request,pk=None):

        mantenimiento = obtener_mantenimiento_por_id(pk)

        aprobado_por = request.data.get("aprobado_por")

        if aprobado_por:
            mantenimiento.aprobado_por_id = aprobado_por

        mantenimiento.estado = "aprobado"
        mantenimiento.save()

        return Response({
            "message":"Mantenimiento aprobado correctamente"
        })
    
class OrdenServicioViewSet(viewsets.ModelViewSet):

    serializer_class = OrdenServicioSerializer

    def get_queryset(self):
        return obtener_ordenes()
    
    def create(self,request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        orden = serializer.save()

        return Response(
            OrdenServicioSerializer(orden).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True,methods=["patch"])
    def cerrar(self,request,pk=None):

        orden = OrdenServicio.objects.get(pk=pk)

        orden.estado = "ejecutado"

        orden.save()

        serializer = self.get_serializer(orden)

        return Response({
            "message":"Orden cerrada correctamente",
            "data":serializer.data
        })
    
 
class ProgramacionMantenimientoViewSet(viewsets.ModelViewSet):

    serializer_class = ProgramacionMantenimientoSerializer

    def get_queryset(self):
        return obtener_programaciones()
    
    def create(self, request):

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "message": "Error al crear la programación",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        programacion = serializer.save()

        programacion.calcularProximaFecha()

        return Response(
            ProgramacionMantenimientoSerializer(programacion).data,
            status=status.HTTP_201_CREATED,
        )
    
    def destroy(self,request,pk=None):

        try:
            programacion = ProgramacionMantenimiento.objects.get(pk=pk)
        except ProgramacionMantenimiento.DoesNotExist:
            return Response(
                {"message":"Programación no encontrada"},
                status=status.HTTP_204_NO_CONTENT
            )

class CertificadoMetrologicoViewSet(viewsets.ModelViewSet):

    serializer_class = CertificadoMetrologicoSerializer

    def get_queryset(self):
        return CertificadoMetrologico.objects.all()
    
    @action(detail=True,methods=["post"])
    def generar_certificado(self,request,pk=None):

        mantenimiento = request.data.get("mantenimiento")
        responsable = request.data.get("responsable")
        numero = request.data.get("numeroCertificado")

        certificado = CertificadoMetrologico.objects.create(
            numeroCertificado = numero,
            responsable_id=responsable,
            mantenimiento_id=mantenimiento
        )  

        serializer = self.get_serializer(certificado)

        return Response({
            "message":"Certificado generado correctamente",
            "data":serializer.data
        },status=status.HTTP_201_CREATED)

class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return obtener_notificaciones()


class ReporteViewSet(viewsets.ModelViewSet):

    serializer_class = ReporteSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = ReporteFilter

    def get_queryset(self):
        return obtener_reportes()

    def retrieve(self, request, pk=None):

        reporte = obtener_reporte_por_id(pk)

        serializer = self.get_serializer(reporte)

        return Response({
            "message":"Reporte encontrado",
            "data":serializer.data
        })
    
    @action(detail=False, methods=["get"],url_path="generar-reporte")
    def generar_reporte(self,request):

        reporte = generar_reporte_general()

        return Response(
            reporte,
            status=status.HTTP_200_OK
        )