from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny

from django.contrib.auth import login 

from .models import Usuario

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UsuarioSerializer
)

from .services import (
    login_usuario,
    register_usuario
)

class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        return Usuario.objects.all()
    

class AuthViewSet(ViewSet):

    permission_classes = [AllowAny]

    def register(self,request):

        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        usuario = register_usuario(serializer.validated_data)

        return Response(
            {
                "message":"Usuario registrado correctamente"
            },
            status=status.HTTP_201_CREATED
        )
    
    def login(self,request):

        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        correo = serializer.validated_data["correo"]
        password = serializer.validated_data["password"]

        user = login_usuario(correo,password)

        if not user:
            return Response(
                {"error":"Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        login(request.user)

        return Response({
            "message":"Login exitoso",
            "usuario":user.nombre,
            "rol":user.rol
        })

