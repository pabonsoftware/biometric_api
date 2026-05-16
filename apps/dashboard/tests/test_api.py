from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.branches.tests.factories import BranchFactory
from apps.equipment.models import EquipmentStatus
from apps.equipment.reliability import recompute_for
from apps.equipment.tests.factories import EquipmentFactory
from apps.failures.models import FailureSeverity
from apps.failures.tests.factories import FailureRecordFactory
from apps.maintenance.models import MaintenanceKind
from apps.maintenance.tests.factories import MaintenanceRecordFactory
from apps.scheduling.models import ScheduledMaintenanceKind
from apps.scheduling.tests.factories import MaintenanceScheduleFactory

pytestmark = pytest.mark.django_db


SUMMARY_URL = reverse("v1:dashboard:summary")


class TestAuth:
    def test_requires_auth(self, api_client):
        assert api_client.get(SUMMARY_URL).status_code == 401


class TestEquipmentKpis:
    def test_counts_by_status(self, auth_client, branch):
        EquipmentFactory(branch=branch, status=EquipmentStatus.ACTIVE)
        EquipmentFactory(branch=branch, status=EquipmentStatus.ACTIVE)
        EquipmentFactory(branch=branch, status=EquipmentStatus.IN_MAINTENANCE)
        EquipmentFactory(branch=branch, status=EquipmentStatus.IN_REPAIR)
        EquipmentFactory(branch=branch, status=EquipmentStatus.INACTIVE)

        body = auth_client.get(SUMMARY_URL).json()
        kpis = body["kpis"]["equipment"]

        assert kpis == {
            "active": 2,
            "in_maintenance": 1,
            "in_repair": 1,
            "inactive": 1,
            "total": 5,
        }


class TestFailuresKpis:
    def test_critical_open_vs_total_open(self, auth_client, equipment):
        FailureRecordFactory(
            equipment=equipment, severity=FailureSeverity.CRITICAL, resolved=False
        )
        FailureRecordFactory(
            equipment=equipment, severity=FailureSeverity.HIGH, resolved=False
        )
        FailureRecordFactory(
            equipment=equipment,
            severity=FailureSeverity.CRITICAL,
            resolved=True,
            resolved_at=timezone.now(),
        )

        kpis = auth_client.get(SUMMARY_URL).json()["kpis"]["failures"]
        assert kpis == {"critical_open": 1, "total_open": 2}


class TestSchedulingKpis:
    def test_next_7_days_ignores_completed_and_far(self, auth_client, equipment):
        today = timezone.localdate()
        MaintenanceScheduleFactory(equipment=equipment, scheduled_date=today)
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=today + timedelta(days=3)
        )
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=today + timedelta(days=30)
        )  # fuera de ventana
        MaintenanceScheduleFactory(
            equipment=equipment,
            scheduled_date=today + timedelta(days=1),
            is_completed=True,
        )

        kpis = auth_client.get(SUMMARY_URL).json()["kpis"]["scheduling"]
        assert kpis["next_7_days"] == 2

    def test_overdue_counts_pending_in_the_past(self, auth_client, equipment):
        today = timezone.localdate()
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=today - timedelta(days=2)
        )
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=today - timedelta(days=10)
        )
        MaintenanceScheduleFactory(
            equipment=equipment,
            scheduled_date=today - timedelta(days=5),
            is_completed=True,
        )  # cumplido, no cuenta

        kpis = auth_client.get(SUMMARY_URL).json()["kpis"]["scheduling"]
        assert kpis["overdue"] == 2


class TestMaintenanceKpis:
    def test_this_month_count_and_cost(self, auth_client, equipment):
        today = timezone.localdate()
        # Mes actual
        MaintenanceRecordFactory(
            equipment=equipment, date=today.replace(day=1), cost=Decimal("100000")
        )
        MaintenanceRecordFactory(
            equipment=equipment, date=today, cost=Decimal("50000")
        )
        # Mes pasado (no debe contar)
        prev_month_day = (today.replace(day=1) - timedelta(days=1))
        MaintenanceRecordFactory(
            equipment=equipment, date=prev_month_day, cost=Decimal("999999")
        )

        kpis = auth_client.get(SUMMARY_URL).json()["kpis"]["maintenance"]
        assert kpis["this_month_count"] == 2
        assert Decimal(kpis["this_month_cost"]) == Decimal("150000")


class TestDistributions:
    def test_equipment_by_status(self, auth_client, branch):
        EquipmentFactory(branch=branch, status=EquipmentStatus.ACTIVE)
        EquipmentFactory(branch=branch, status=EquipmentStatus.IN_REPAIR)

        body = auth_client.get(SUMMARY_URL).json()
        dist = {row["status"]: row["count"] for row in body["distributions"]["equipment_by_status"]}
        assert dist[EquipmentStatus.ACTIVE] == 1
        assert dist[EquipmentStatus.IN_REPAIR] == 1
        assert dist[EquipmentStatus.IN_MAINTENANCE] == 0

    def test_failures_by_severity(self, auth_client, equipment):
        FailureRecordFactory(
            equipment=equipment, severity=FailureSeverity.HIGH, resolved=False
        )
        FailureRecordFactory(
            equipment=equipment,
            severity=FailureSeverity.HIGH,
            resolved=True,
            resolved_at=timezone.now(),
        )

        body = auth_client.get(SUMMARY_URL).json()
        by_sev = {
            row["severity"]: row
            for row in body["distributions"]["failures_by_severity"]
        }
        assert by_sev[FailureSeverity.HIGH] == {
            "severity": FailureSeverity.HIGH,
            "open": 1,
            "resolved": 1,
        }


class TestTimeSeries:
    def test_six_months_with_gaps_filled(self, auth_client, equipment):
        today = timezone.localdate()
        # Crear mantenimientos en el mes actual y hace 2 meses; el mes intermedio
        # debe aparecer con ceros.
        MaintenanceRecordFactory(
            equipment=equipment,
            kind=MaintenanceKind.PREVENTIVE,
            date=today,
            cost=Decimal("100"),
        )
        two_months_ago = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        two_months_ago = (two_months_ago - timedelta(days=1)).replace(day=1)
        MaintenanceRecordFactory(
            equipment=equipment,
            kind=MaintenanceKind.CORRECTIVE,
            date=two_months_ago,
            cost=Decimal("200"),
        )

        series = auth_client.get(SUMMARY_URL).json()["time_series"][
            "maintenance_by_month"
        ]
        assert len(series) == 6
        months = [row["month"] for row in series]
        assert months == sorted(months)  # orden ascendente

        current_key = today.isoformat()[:7]
        current_row = next(r for r in series if r["month"] == current_key)
        assert current_row["PREVENTIVE"] == 1
        assert current_row["CORRECTIVE"] == 0
        assert Decimal(current_row["cost"]) == Decimal("100")


class TestLists:
    def test_overdue_schedules_limit_and_order(self, auth_client, equipment):
        today = timezone.localdate()
        for i in range(12):
            MaintenanceScheduleFactory(
                equipment=equipment, scheduled_date=today - timedelta(days=i + 1)
            )

        items = auth_client.get(SUMMARY_URL).json()["lists"]["overdue_schedules"]
        assert len(items) == 10
        dates = [date.fromisoformat(it["scheduled_date"]) for it in items]
        assert dates == sorted(dates)
        assert items[0]["days_overdue"] >= 1

    def test_worst_mtbf_requires_at_least_two_failures(self, auth_client, branch):
        eq_one = EquipmentFactory(branch=branch)
        FailureRecordFactory(equipment=eq_one)  # 1 sola → mtbf None
        recompute_for(eq_one)

        eq_two = EquipmentFactory(branch=branch)
        base = timezone.now() - timedelta(hours=100)
        for delta in (0, 48):
            f = FailureRecordFactory(equipment=eq_two)
            f.reported_at = base + timedelta(hours=delta)
            f.save(update_fields=["reported_at"])
        recompute_for(eq_two)

        worst = auth_client.get(SUMMARY_URL).json()["lists"]["worst_mtbf"]
        names = [w["asset_tag"] for w in worst]
        assert eq_two.asset_tag in names
        assert eq_one.asset_tag not in names


class TestMyTasks:
    def test_schedules_filtered_by_user_assignment(
        self, api_client, tecnico, ingeniero, equipment
    ):
        today = timezone.localdate()
        mine = MaintenanceScheduleFactory(
            equipment=equipment,
            scheduled_date=today + timedelta(days=2),
            assigned_technician=tecnico,
            kind=ScheduledMaintenanceKind.PREVENTIVE,
        )
        MaintenanceScheduleFactory(
            equipment=equipment,
            scheduled_date=today + timedelta(days=3),
            assigned_engineer=ingeniero,
        )  # del ingeniero, no del técnico
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=today + timedelta(days=4)
        )  # sin asignar

        api_client.force_authenticate(user=tecnico)
        body = api_client.get(SUMMARY_URL).json()

        ids = [s["id"] for s in body["my_tasks"]["schedules"]]
        assert ids == [mine.id]

    def test_failures_empty_in_v1(self, auth_client, equipment):
        FailureRecordFactory(equipment=equipment)
        body = auth_client.get(SUMMARY_URL).json()
        assert body["my_tasks"]["failures"] == []


@pytest.fixture
def branch(db):
    return BranchFactory()


@pytest.fixture
def equipment(db, branch):
    return EquipmentFactory(branch=branch)
