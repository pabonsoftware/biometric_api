from rest_framework import serializers
from .models import Usuario

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
            "rol"
        ]

    def create(self,validated_data):

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

class ResetPassword(serializers.Serializer):

    token = serializers.CharField()

    new_password = serializers.CharField()