import factory
from factory.django import DjangoModelFactory

from apps.equipment.tests.factories import EquipmentFactory
from apps.failures.models import FailureRecord, FailureSeverity


class FailureRecordFactory(DjangoModelFactory):
    class Meta:
        model = FailureRecord

    equipment = factory.SubFactory(EquipmentFactory)
    description = factory.Faker("sentence", nb_words=10)
    severity = FailureSeverity.MEDIUM
    resolved = False
    resolved_at = None
    resolution_notes = ""
