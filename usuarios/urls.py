from django.urls import path 
from .views import AuthViewSet,UsuarioViewSet



urlpatterns = [
    path('usuarios/',UsuarioViewSet.as_view({"get":"list"})),
    path("auth/login/",AuthViewSet.as_view({"post":"login"})),
    path("auth/register/",AuthViewSet.as_view({"post":"register"})),
    path("auth/recovery-password/",AuthViewSet.as_view({"post":"recovery_password"})),
    path("auth/reset-password",AuthViewSet.as_view({"post":"reset_password"}))
]