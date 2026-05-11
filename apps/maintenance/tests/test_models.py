from datetime import date

import pytest

from apps.maintenance.models import MaintenanceKind, MaintenanceRecord

from .factories import MaintenanceRecordFactory

pytestmark = pytest.mark.django_db


class TestMaintenanceRecordModel:
    def test_str_format(self, equipment):
        record = MaintenanceRecordFactory(
            equipment=equipment,
            kind=MaintenanceKind.PREVENTIVE,
            date=date(2026, 3, 10),
        )
        assert str(record) == f"Mantenimiento preventivo - {equipment.asset_tag} - 2026-03-10"

    def test_default_ordering_is_date_desc_then_created_desc(self, equipment):
        old = MaintenanceRecordFactory(equipment=equipment, date=date(2025, 1, 1))
        new = MaintenanceRecordFactory(equipment=equipment, date=date(2026, 1, 1))
        mid = MaintenanceRecordFactory(equipment=equipment, date=date(2025, 6, 1))

        ids = list(MaintenanceRecord.objects.values_list("id", flat=True))

        assert ids == [new.id, mid.id, old.id]


class TestMaintenanceRecordManager:
    def test_for_equipment_filters_by_equipment(self, equipment, branch):
        from apps.equipment.tests.factories import EquipmentFactory

        other = EquipmentFactory(branch=branch)
        MaintenanceRecordFactory.create_batch(2, equipment=equipment)
        MaintenanceRecordFactory(equipment=other)

        qs = MaintenanceRecord.objects.for_equipment(equipment.id)

        assert qs.count() == 2

    def test_preventive_returns_only_preventive(self, equipment):
        MaintenanceRecordFactory(equipment=equipment, kind=MaintenanceKind.PREVENTIVE)
        MaintenanceRecordFactory(equipment=equipment, kind=MaintenanceKind.CORRECTIVE)

        assert MaintenanceRecord.objects.preventive().count() == 1

    def test_in_range_filters_by_date_range(self, equipment):
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 1, 1))
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 6, 15))
        MaintenanceRecordFactory(equipment=equipment, date=date(2026, 1, 1))

        qs = MaintenanceRecord.objects.in_range(date(2025, 1, 1), date(2025, 12, 31))

        assert qs.count() == 2
