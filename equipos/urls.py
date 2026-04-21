from rest_framework.routers import DefaultRouter

from .views import EquipoBiomedicoViewSet

router = DefaultRouter()

router.register(r"equipos",EquipoBiomedicoViewSet,basename='equipos')

urlpatterns = router.urls