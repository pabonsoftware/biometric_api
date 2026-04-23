from django.urls import path 
from .views import AuthViewSet,UsuarioViewSet



urlpatterns = [
    path('usuarios/',UsuarioViewSet.as_view({"get":"list"})),
    path("login/",AuthViewSet.as_view({"post":"login"})),
    path("register/",AuthViewSet.as_view({"post":"register"}))
]