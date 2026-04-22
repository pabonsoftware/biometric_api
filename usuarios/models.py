from django.db import models
from django.contrib.auth.models import AbstractUser

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

    username = None 

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

    REQUIRED_FIELDS = ["nombre"]

    def __str__(self):
        return f"{self.nombre}- {self.rol}"