import factory
from factory.django import DjangoModelFactory

from apps.catalog.models import Brand, EquipmentModel


class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Brand

    name = factory.Sequence(lambda n: f"Brand {n}")
    is_active = True


class EquipmentModelFactory(DjangoModelFactory):
    class Meta:
        model = EquipmentModel

    brand = factory.SubFactory(BrandFactory)
    name = factory.Sequence(lambda n: f"M-{n:04d}")
    description = factory.Faker("sentence", nb_words=8)
    is_active = True
