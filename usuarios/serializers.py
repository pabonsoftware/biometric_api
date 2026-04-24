from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, UserAudit


class UsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario

        fields = [
            "id",
            "nombre",
            "correo",
            "password",
            "rol",
            "username",
        ]

    def create(self, validated_data):
        password = validated_data.get("password")
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):

    correo = serializers.EmailField()
    password = serializers.CharField()


class RecoveryPasswordSerializer(serializers.Serializer):

    correo = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):

    token = serializers.CharField()
    new_password = serializers.CharField()


class AdminListSerializer(serializers.ModelSerializer):
    """Serializer to list admins with basic info."""

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nombre',
            'correo',
            'rol',
            'estado',
            'date_joined',
            'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer to create new admins."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Contraseña segura para el administrador"
    )

    class Meta:
        model = Usuario
        fields = [
            'nombre',
            'correo',
            'rol',
            'password',
            'estado'
        ]

    def validate_correo(self, value):
        """Validate that email is unique."""
        if Usuario.objects.filter(correo=value.lower()).exists():
            raise serializers.ValidationError(
                "Este correo ya está registrado en el sistema"
            )
        return value.lower()

    def validate_rol(self, value):
        """Validate that role is valid for admin."""
        if value not in ['superadministrador', 'administrador']:
            raise serializers.ValidationError(
                "El rol debe ser 'superadministrador' o 'administrador'"
            )
        return value

    def validate_estado(self, value):
        """Validate that status is valid."""
        if value not in ['activo', 'inactivo']:
            raise serializers.ValidationError(
                "El estado debe ser 'activo' o 'inactivo'"
            )
        return value


class AdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer to update admins."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        validators=[validate_password],
        help_text="Dejar en blanco para no cambiar la contraseña"
    )

    class Meta:
        model = Usuario
        fields = [
            'nombre',
            'correo',
            'rol',
            'estado',
            'password'
        ]

    def validate_correo(self, value):
        """Validate that email is unique (except for current user)."""
        current_user = self.instance
        if Usuario.objects.filter(correo=value.lower()).exclude(id=current_user.id).exists():
            raise serializers.ValidationError(
                "Este correo ya está registrado en el sistema"
            )
        return value.lower()

    def validate_rol(self, value):
        """Validate that role is valid for admin."""
        if value not in ['superadministrador', 'administrador']:
            raise serializers.ValidationError(
                "El rol debe ser 'superadministrador' o 'administrador'"
            )
        return value

    def validate_estado(self, value):
        """Validate that status is valid."""
        if value not in ['activo', 'inactivo']:
            raise serializers.ValidationError(
                "El estado debe ser 'activo' o 'inactivo'"
            )
        return value


class UserAuditSerializer(serializers.ModelSerializer):
    """Serializer for audit log."""

    actor_name = serializers.CharField(
        source='actor.nombre',
        read_only=True
    )
    actor_email = serializers.CharField(
        source='actor.correo',
        read_only=True
    )
    target_user_name = serializers.CharField(
        source='target_user.nombre',
        read_only=True
    )

    class Meta:
        model = UserAudit
        fields = [
            'id',
            'action_type',
            'actor',
            'actor_name',
            'actor_email',
            'target_user',
            'target_user_name',
            'details',
            'created_at'
        ]
        read_only_fields = fields