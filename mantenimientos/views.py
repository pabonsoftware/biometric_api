"""
API views for maintenance operations.

Implements REST endpoints for maintenance CRUD, status changes, and reporting.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    MantenimientoSerializer,
    MantenimientoCreateSerializer,
    MantenimientoUpdateSerializer,
    CertificadoMetrologicoSerializer,
    OrdenServicioSerializer,
    OrdenServicioWriteSerializer,
    ProgramacionMantenimientoSerializer,
    ReporteSerializer,
    ReporteWriteSerializer
)

from .selectors import (
    obtener_mantenimientos,
    obtener_mantenimiento_por_id,
    obtener_ordenes,
    obtener_programaciones,
    obtener_reportes,
    obtener_reporte_por_id,
)

from .services import (
    crear_mantenimiento,
    editar_mantenimiento,
    cambiar_estado,
    obtener_mantenimiento,
    supervisar_mantenimiento,
    generar_reporte_general
)

from .models import (
    CertificadoMetrologico,
    ProgramacionMantenimiento,
    OrdenServicio,
    Mantenimiento
)

from .filters import (
    MantenimientoFilter,
    ReporteFilter
)

from .permissions import (
    IsAuthenticatedAndActive,
    CanApproveOrSupervise,
    CanViewMaintenance,
    IsIngenierOrTecnico
)

from .exceptions import (
    MantenimientoNotFound,
    EstadoInvalido,
    DatosInvalidos
)


class MantenimientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for maintenance CRUD operations.

    Provides:
    - list: GET /api/mantenimientos/ - List all maintenance records
    - create: POST /api/mantenimientos/ - Create new maintenance
    - retrieve: GET /api/mantenimientos/{id}/ - Get specific maintenance
    - update: PATCH /api/mantenimientos/{id}/ - Update maintenance
    - destroy: DELETE /api/mantenimientos/{id}/ - Delete maintenance
    - cambiar_estado: PATCH /api/mantenimientos/{id}/cambiar_estado/ - Change state
    - supervisar: GET /api/mantenimientos/{id}/supervisar/ - Approve/Supervise
    - por_equipo: GET /api/mantenimientos/equipo/{equipo_id}/ - Maintenance history by equipment
    """

    filter_backends = [DjangoFilterBackend]
    filterset_class = MantenimientoFilter
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return MantenimientoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MantenimientoUpdateSerializer
        return MantenimientoSerializer

    def get_queryset(self):
        """Get queryset with proper select_related for performance."""
        queryset = obtener_mantenimientos()

        # Filter by equipment if specified
        equipo_id = self.request.query_params.get('equipo_id')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)

        # Filter by responsible if specified
        responsable_id = self.request.query_params.get('responsable_id')
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)

        # Filter by status if specified
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    def retrieve(self, request, pk=None):
        """Get a specific maintenance record."""
        try:
            mantenimiento = obtener_mantenimiento(pk)
        except MantenimientoNotFound:
            return Response(
                {"error": f"Mantenimiento con ID {pk} no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(mantenimiento)
        return Response(serializer.data)

    def create(self, request):
        """Create a new maintenance record."""
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mantenimiento = crear_mantenimiento(**serializer.validated_data)
            return Response(
                MantenimientoSerializer(mantenimiento).data,
                status=status.HTTP_201_CREATED
            )
        except DatosInvalidos as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, pk=None):
        """Update a maintenance record."""
        try:
            mantenimiento = obtener_mantenimiento(pk)
        except MantenimientoNotFound:
            return Response(
                {"error": f"Mantenimiento con ID {pk} no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mantenimiento_actualizado = editar_mantenimiento(
                pk,
                serializer.validated_data,
                actor=request.user
            )
            return Response(
                MantenimientoSerializer(mantenimiento_actualizado).data,
                status=status.HTTP_200_OK
            )
        except DatosInvalidos as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAuthenticatedAndActive, CanApproveOrSupervise])
    def cambiar_estado(self, request, pk=None):
        """
        Change the state of a maintenance record.

        PATCH body:
        {
            "nuevo_estado": "en_proceso|completado|aprobado|supervisado|ejecutado",
            "aprobado_por_id": <optional user_id>
        }
        """
        try:
            mantenimiento = obtener_mantenimiento(pk)
        except MantenimientoNotFound:
            return Response(
                {"error": f"Mantenimiento con ID {pk} no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        nuevo_estado = request.data.get('nuevo_estado')
        if not nuevo_estado:
            return Response(
                {"error": "nuevo_estado es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        aprobado_por = None
        if 'aprobado_por_id' in request.data:
            aprobado_por_id = request.data.get('aprobado_por_id')
            if aprobado_por_id:
                from usuarios.models import Usuario
                try:
                    aprobado_por = Usuario.objects.get(id=aprobado_por_id)
                except Usuario.DoesNotExist:
                    return Response(
                        {"error": f"Usuario con ID {aprobado_por_id} no existe."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        try:
            mantenimiento_actualizado = cambiar_estado(
                pk,
                nuevo_estado,
                aprobado_por=aprobado_por
            )
            return Response(
                MantenimientoSerializer(mantenimiento_actualizado).data,
                status=status.HTTP_200_OK
            )
        except EstadoInvalido as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAuthenticatedAndActive, CanApproveOrSupervise])
    def supervisar(self, request, pk=None):
        """
        Approve/supervise a maintenance record and retrieve associated programming.

        Returns the maintenance record and related programming schedules.
        """
        try:
            aprobado_por_id = request.query_params.get('aprobado_por')
            programaciones = supervisar_mantenimiento(pk, aprobado_por_id)
            serializer = ProgramacionMantenimientoSerializer(programaciones, many=True)

            return Response({
                "message": "Mantenimiento supervisado correctamente",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except MantenimientoNotFound:
            return Response(
                {"error": f"Mantenimiento con ID {pk} no existe."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='por-equipo/(?P<equipo_id>[^/.]+)')
    def por_equipo(self, request, equipo_id=None):
        """
        Get maintenance history for a specific equipment.

        GET /api/mantenimientos/por-equipo/{equipo_id}/
        """
        try:
            from mantenimientos.services import listar_por_equipo
            mantenimientos = listar_por_equipo(int(equipo_id))
            serializer = MantenimientoSerializer(mantenimientos, many=True)
            return Response({
                "count": mantenimientos.count(),
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrdenServicioViewSet(viewsets.ModelViewSet):
    """ViewSet for service orders (órdenes de servicio)."""

    serializer_class = OrdenServicioSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive]

    def get_queryset(self):
        return obtener_ordenes()

    def create(self, request):
        """Create a new service order."""
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        orden = serializer.save()

        return Response(
            OrdenServicioSerializer(orden).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def cerrar(self, request, pk=None):
        """Close/execute a service order."""
        try:
            orden = OrdenServicio.objects.get(pk=pk)
            orden.estado = "ejecutada"
            orden.save()

            serializer = self.get_serializer(orden)

            return Response({
                "message": "Orden cerrada correctamente",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except OrdenServicio.DoesNotExist:
            return Response(
                {"error": f"Orden con ID {pk} no existe."},
                status=status.HTTP_404_NOT_FOUND
            )


class ProgramacionMantenimientoViewSet(viewsets.ModelViewSet):
    """ViewSet for maintenance scheduling (programaciones)."""

    serializer_class = ProgramacionMantenimientoSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive, CanApproveOrSupervise]

    def get_queryset(self):
        return obtener_programaciones()

    def create(self, request):
        """Create a new maintenance schedule."""
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
        programacion.calcular_proxima_fecha()

        return Response(
            ProgramacionMantenimientoSerializer(programacion).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, pk=None):
        """Delete a maintenance schedule."""
        try:
            programacion = ProgramacionMantenimiento.objects.get(pk=pk)
            programacion.delete()
            return Response(
                {"message": "Programación eliminada correctamente"},
                status=status.HTTP_204_NO_CONTENT
            )
        except ProgramacionMantenimiento.DoesNotExist:
            return Response(
                {"error": "Programación no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )


class CertificadoMetrologicoViewSet(viewsets.ModelViewSet):
    """ViewSet for metrological certificates."""

    serializer_class = CertificadoMetrologicoSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive]

    def get_queryset(self):
        return CertificadoMetrologico.objects.all()

    @action(detail=True, methods=['post'])
    def generar_certificado(self, request, pk=None):
        """Generate a metrological certificate."""
        mantenimiento = request.data.get("mantenimiento")
        responsable = request.data.get("responsable")
        numero = request.data.get("numeroCertificado")

        certificado = CertificadoMetrologico.objects.create(
            numero_certificado=numero,
            responsable_id=responsable,
            mantenimiento_id=mantenimiento
        )

        serializer = self.get_serializer(certificado)

        return Response({
            "message": "Certificado generado correctamente",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for notifications (read-only)."""

    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive]

    def get_queryset(self):
        return obtener_notificaciones()


class ReporteViewSet(viewsets.ModelViewSet):
    """ViewSet for maintenance reports."""

    serializer_class = ReporteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReporteFilter
    permission_classes = [IsAuthenticated, IsAuthenticatedAndActive]

    def get_queryset(self):
        return obtener_reportes()
    
    def get_serializer_class(self):
        if self.action in ["create","update","partial_update"]:
            return ReporteWriteSerializer
        return ReporteSerializer

    def retrieve(self, request, pk=None):
        """Get a specific report."""
        reporte = obtener_reporte_por_id(pk)

        serializer = ReporteSerializer(reporte)

        return Response({
            "message": "Reporte encontrado",
            "data": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='generar-reporte')
    def generar_reporte(self, request):
        """Generate general maintenance report."""
        reporte = generar_reporte_general()

        return Response(
            reporte,
            status=status.HTTP_200_OK
        )
