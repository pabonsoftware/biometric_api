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
    obtener_notificaciones,
    obtener_reportes,
    obtener_reporte_por_id
)

from .services import (
    crear_mantenimiento,
    actualizar_mantenimiento,
    eliminar_mantenimiento,
    supervisar_mantenimiento,
    generar_reporte_general
)

from .models import (
    CertificadoMetrologico,
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
    

    def destroy(self,request,pk=None):

        mantenimiento = obtener_mantenimiento_por_id(pk)

        eliminar_mantenimiento(mantenimiento)

        return Response(
            {
                "message":"Mantenimiento eliminado correctamente"
            }
        )
    
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

class CertificadoMetrologicoViewSet(viewsets.ModelViewSet):

    serializer_class = CertificadoMetrologicoSerializer

    def get_queryset(self):
        return CertificadoMetrologico.objects.all()
   

class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return obtener_notificaciones()


class ReporteGeneralViewSet(viewsets.ModelViewSet):

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