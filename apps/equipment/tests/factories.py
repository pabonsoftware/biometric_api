import factory
from factory.django import DjangoModelFactory

from apps.branches.tests.factories import BranchFactory
from apps.catalog.tests.factories import EquipmentModelFactory
from apps.equipment.models import Equipment, EquipmentStatus


class EquipmentFactory(DjangoModelFactory):
    class Meta:
        model = Equipment

    name = factory.Sequence(lambda n: f"Equipo {n}")
    asset_tag = factory.Sequence(lambda n: f"EQ-{n:04d}")
    equipment_model = factory.SubFactory(EquipmentModelFactory)
    branch = factory.SubFactory(BranchFactory)
    location = ""
    purchase_date = None
    status = EquipmentStatus.ACTIVE
    risk_class = None
