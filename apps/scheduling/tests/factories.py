from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory

from apps.equipment.tests.factories import EquipmentFactory
from apps.scheduling.models import MaintenanceSchedule, ScheduledMaintenanceKind


class MaintenanceScheduleFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceSchedule

    equipment = factory.SubFactory(EquipmentFactory)
    kind = ScheduledMaintenanceKind.PREVENTIVE
    scheduled_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    notes = factory.Faker("sentence", nb_words=8)
    is_completed = False
