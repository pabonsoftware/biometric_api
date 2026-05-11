import factory
from factory.django import DjangoModelFactory

from apps.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = "Nombre"
    last_name = "Apellido"
    role = User.Role.TECNICO
    phone = ""
    is_active = True
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class SuperadminFactory(UserFactory):
    role = User.Role.SUPERADMIN
    is_staff = True
    is_superuser = True


class AdminFactory(UserFactory):
    role = User.Role.ADMIN


class CoordinadorFactory(UserFactory):
    role = User.Role.COORDINADOR


class IngenieroFactory(UserFactory):
    role = User.Role.INGENIERO


class TecnicoFactory(UserFactory):
    role = User.Role.TECNICO
