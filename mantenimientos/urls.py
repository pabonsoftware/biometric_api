from django.urls import path,include
from rest_framework.routers import DefaultRouter

from .views import (
    MantenimientoViewSet,
    ProgramacionMantenimientoViewSet,
    NotificacionViewSet,
    OrdenServicioViewSet,
    CertificadoMetrologicoViewSet,
    ReporteGeneralViewSet
)

router = DefaultRouter()

router.register(r'mantenimientos',MantenimientoViewSet, basename='mantenimientos')
router.register(r'programaciones',ProgramacionMantenimientoViewSet,basename='programaciones')
router.register(r'ordenes-servicio',OrdenServicioViewSet,basename='ordenes')
router.register(r'certificados',CertificadoMetrologicoViewSet,basename='certificados')
router.register(r'notificaciones',NotificacionViewSet,basename='notificaciones')
router.register(r'reportes',ReporteGeneralViewSet, basename='reportes')

urlpatterns = [
    path('',include(router.urls)),
]