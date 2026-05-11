import factory
from factory.django import DjangoModelFactory

from apps.branches.models import Branch
from apps.users.tests.factories import UserFactory  # noqa: F401  (re-exportado)


class BranchFactory(DjangoModelFactory):
    class Meta:
        model = Branch

    name = factory.Sequence(lambda n: f"Branch {n}")
    address = factory.Faker("street_address")
    city = factory.Iterator(["Bogota", "Medellin", "Cali", "Barranquilla"])
    phone = factory.Sequence(lambda n: f"+57 300 000 {n:04d}")
    email = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '')}@clinic.test")
    is_active = True
