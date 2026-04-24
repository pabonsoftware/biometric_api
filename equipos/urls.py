from rest_framework.routers import DefaultRouter

from .views import EquipoBiomedicoViewSet, MarcaViewSet, ModeloViewSet, FallaViewSet

router = DefaultRouter()

router.register(r"equipos", EquipoBiomedicoViewSet, basename='equipos')
router.register(r"marcas", MarcaViewSet, basename='marcas')
router.register(r"modelos", ModeloViewSet, basename='modelos')
router.register(r"fallas", FallaViewSet, basename='fallas')

urlpatterns = router.urls