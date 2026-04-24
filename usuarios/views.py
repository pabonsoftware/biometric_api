from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .utils.token import generar_token
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import login

from .models import (
    Usuario,
    PasswordResetToken,
    UserAudit
)

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UsuarioSerializer,
    RecoveryPasswordSerializer,
    ResetPasswordSerializer,
    AdminListSerializer,
    AdminCreateSerializer,
    AdminUpdateSerializer,
    UserAuditSerializer
)

from .services import (
    login_usuario,
    register_usuario,
    send_alert_email,
    create_admin,
    edit_admin,
    deactivate_admin,
    activate_admin
)

from .permissions import IsSuperAdmin, IsActive
from .selectors import (
    get_admins,
    get_admin_by_id,
    get_user_audit_log
)


class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        return Usuario.objects.all()


class AuthViewSet(ViewSet):

    permission_classes = [AllowAny]

    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = register_usuario(serializer.validated_data)
        return Response(
            {"message": "Usuario registrado correctamente"},
            status=status.HTTP_201_CREATED
        )

    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correo = serializer.validated_data["correo"]
        password = serializer.validated_data["password"]

        user = login_usuario(correo, password)

        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login exitoso",
            "usuario": user.nombre,
            "rol": user.rol,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

    @action(detail=False, methods=["post"], url_path="recovery_password")
    def recovery_password(self, request):
        serializer = RecoveryPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correo = serializer.validated_data["correo"]
        user = Usuario.objects.filter(correo=correo).first()

        if not user:
            return Response({"error": "Correo no encontrado"}, status=400)

        token = generar_token()
        PasswordResetToken.objects.create(usuario=user, token=token)

        link = f"http://localhost:3000/auth/reset-password?token={token}"
        mensaje = f"""
        Hola {user.nombre},

        Para recuperar tu contraseña haz clic en el siguiente enlace:

        {link}

        Si no solicitaste esto, ignora este mensaje
        """

        send_alert_email(user.correo, mensaje)

        return Response({"message": "Correo de recuperación enviada"})

    @action(detail=False, methods=["post"], url_path='reset-password')
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        registro = PasswordResetToken.objects.filter(token=token).first()

        if not registro:
            return Response({"error": "Token inválido"}, status=400)

        if registro.creado < timezone.now() - timedelta(hours=1):
            return Response({"error": "Token expirado"}, status=400)

        user = registro.usuario
        user.set_password(new_password)
        user.save()
        registro.delete()

        return Response({"message": "Contraseña actualizada correctamente"})


class AdminViewSet(viewsets.ModelViewSet):
    """ViewSet for system admin management."""

    permission_classes = [IsAuthenticated, IsActive, IsSuperAdmin]
    queryset = get_admins()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AdminCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUpdateSerializer
        elif self.action == 'audit_log':
            return UserAuditSerializer
        return AdminListSerializer

    def list(self, request, *args, **kwargs):
        """List all system admins."""
        queryset = get_admins()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create a new admin."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            usuario = create_admin(
                serializer.validated_data,
                actor=request.user
            )
            output_serializer = AdminListSerializer(usuario)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            raise ValidationError({"error": str(e)})

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Get details of a specific admin."""
        usuario = get_admin_by_id(pk)
        if not usuario:
            return Response(
                {"error": "Administrador no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(usuario)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        """Update admin information."""
        usuario = get_admin_by_id(pk)
        if not usuario:
            return Response(
                {"error": "Administrador no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(usuario, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            usuario_actualizado = edit_admin(
                pk,
                serializer.validated_data,
                actor=request.user
            )
            output_serializer = AdminListSerializer(usuario_actualizado)
            return Response(output_serializer.data)
        except ValueError as e:
            raise ValidationError({"error": str(e)})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Deactivate an admin account."""
        usuario = get_admin_by_id(pk)
        if not usuario:
            return Response(
                {"error": "Administrador no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            usuario_deactivated = deactivate_admin(
                pk,
                actor=request.user
            )
            serializer = AdminListSerializer(usuario_deactivated)
            return Response({
                "message": "Administrador desactivado exitosamente",
                "usuario": serializer.data
            })
        except ValueError as e:
            raise ValidationError({"error": str(e)})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Reactivate an admin account."""
        usuario = get_admin_by_id(pk)
        if not usuario:
            return Response(
                {"error": "Administrador no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            usuario_activated = activate_admin(
                pk,
                actor=request.user
            )
            serializer = AdminListSerializer(usuario_activated)
            return Response({
                "message": "Administrador activado exitosamente",
                "usuario": serializer.data
            })
        except ValueError as e:
            raise ValidationError({"error": str(e)})

    @action(detail=True, methods=['get'], url_path='audit-log')
    def audit_log(self, request, pk=None):
        """Get audit log history of an admin."""
        usuario = get_admin_by_id(pk)
        if not usuario:
            return Response(
                {"error": "Administrador no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        audits = get_user_audit_log(pk)
        serializer = UserAuditSerializer(audits, many=True)
        return Response({
            "usuario": usuario.correo,
            "historial": serializer.data
        })

