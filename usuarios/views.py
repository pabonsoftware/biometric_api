from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from .utils.token import generar_token
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import login 

from .models import (
    Usuario,
    PasswordResetToken
)

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UsuarioSerializer,
    RecoveryPasswordSerializer,
    ResetPasswordSerializer
)

from .services import (
    login_usuario,
    register_usuario,
    enviar_alerta_correo
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
    
    @action(detail=False,methods=["post"],url_path="recovery_password")
    def recovery_password(self,request):

        serializer = RecoveryPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correo = serializer.validated_data["correo"]

        user = Usuario.objects.filter(correo=correo).first()

        if not user:
            return Response({"error":"Correo no encontrado"},status=400)
        
        token = generar_token()

        PasswordResetToken.objects.create(
            usuario=user,
            token=token
        )

        link = f"http://localhost:3000/auth/reset-password?token={token}"

        mensaje = f"""

        Hola {user.nombre},

        Para recuperar tu contraseña haz clic en el siguiente enlace:

        {link}

        Si no solicitaste esto, ignora este mensaje
        """

        enviar_alerta_correo(user.correo,mensaje)

        return Response({
            "message":"Correo de recuperación enviada"
        })
    
    @action(detail=False,methods=["post"],url_path='reset-password')
    def reset_password(self,request):

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        registro = PasswordResetToken.objects.filter(token=token).first()

        if not registro:
            return Response({"error":"Token inválido"},status=400)
        
        if registro.creado < timezone.now() - timedelta(hours=1):
            return Response({"error":"Token expirado"},status=400)
        
        user = registro.usuario
        user.set_password(new_password)
        user.save()

        registro.delete()

        return Response({
            "message":"Contraseña actualizada correctamente"
        })

