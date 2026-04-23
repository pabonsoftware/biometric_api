from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UsuarioManager(BaseUserManager):

    def create_user(self,correo,username,nombre,password=None, **extra_fields):

        if not correo:
            raise ValueError("El usuario debe tener un correo")
        
        correo = self.normalize_email(correo)

        user = self.model(
            correo=correo,
            username=username,
            nombre=nombre,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user 
    
    def create_superuser(self,correo,username,nombre,password=None, **extra_fields):

        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)

        return self.create_user(
            correo,
            username,
            nombre,
            password,
            **extra_fields
        )
    
class Usuario(AbstractUser):

    ROLES_CHOICES = [
        ('superadministrador','SUPERADMINISTRADOR'),
        ('administrador','ADMINISTRADOR'),
        ('coordinador','COORDINADOR'),
        ('ingenierobiomedico','INGENIEROBIOMEDICO'),
        ('tecnicobiomedico','TECNICOBIOMEDICO')
    ]

    ESTADO_CHOICES = [
        ("activo","ACTIVO"),
        ("inactivo","INACTIVO")
    ]

    nombre = models.CharField(max_length=100)

    correo = models.EmailField(unique=True)

    rol = models.CharField(
        max_length=50,
        choices=ROLES_CHOICES
    )

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES
    )

    USERNAME_FIELD = "correo"

    REQUIRED_FIELDS = ["username","nombre"]

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombre}- {self.rol}"
    
class PasswordResetToken(models.Model):

    usuario = models.ForeignKey(Usuario,on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.correo} - {self.token}"