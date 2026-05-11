from datetime import date, timedelta
from unittest import mock

import pytest
from django.urls import reverse

from apps.equipment.models import EquipmentStatus
from apps.equipment.tests.factories import EquipmentFactory
from apps.scheduling.models import MaintenanceSchedule, ScheduledMaintenanceKind

from .factories import MaintenanceScheduleFactory

pytestmark = pytest.mark.django_db


LIST_URL = reverse("v1:scheduling:maintenance-list")


def detail_url(pk: int) -> str:
    return reverse("v1:scheduling:maintenance-detail", args=[pk])


def complete_url(pk: int) -> str:
    return reverse("v1:scheduling:maintenance-complete", args=[pk])


def notify_url(pk: int) -> str:
    return reverse("v1:scheduling:maintenance-notify", args=[pk])


class TestSchedulingAuth:
    def test_list_requires_auth(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401

    def test_create_requires_auth(self, api_client, equipment):
        payload = {
            "equipment": equipment.id,
            "kind": ScheduledMaintenanceKind.PREVENTIVE,
            "scheduled_date": (date.today() + timedelta(days=10)).isoformat(),
        }
        assert api_client.post(LIST_URL, payload, format="json").status_code == 401


class TestScheduleCreate:
    def _payload(self, equipment, **overrides):
        data = {
            "equipment": equipment.id,
            "kind": ScheduledMaintenanceKind.PREVENTIVE,
            "scheduled_date": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Calibración trimestral según ficha técnica.",
        }
        data.update(overrides)
        return data

    def test_create_returns_201(self, auth_client, equipment):
        response = auth_client.post(LIST_URL, self._payload(equipment), format="json")

        assert response.status_code == 201
        body = response.json()
        assert body["equipment"] == equipment.id
        assert body["equipment_asset_tag"] == equipment.asset_tag
        assert body["branch_name"] == equipment.branch.name
        assert body["is_completed"] is False
        assert MaintenanceSchedule.objects.count() == 1

    def test_create_strips_notes(self, auth_client, equipment):
        response = auth_client.post(
            LIST_URL,
            self._payload(equipment, notes="   Calibración    "),
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["notes"] == "Calibración"

    def test_create_with_past_date_returns_400(self, auth_client, equipment):
        past = (date.today() - timedelta(days=1)).isoformat()
        response = auth_client.post(
            LIST_URL, self._payload(equipment, scheduled_date=past), format="json"
        )
        assert response.status_code == 400
        assert "La fecha programada no puede ser pasada." in response.json()[
            "scheduled_date"
        ][0]

    def test_create_with_inactive_equipment_returns_400(self, auth_client, branch):
        eq = EquipmentFactory(branch=branch, status=EquipmentStatus.INACTIVE)
        response = auth_client.post(LIST_URL, self._payload(eq), format="json")
        assert response.status_code == 400
        assert "El equipo no está disponible para programación." in response.json()[
            "equipment"
        ][0]

    def test_create_missing_required_returns_400(self, auth_client):
        response = auth_client.post(LIST_URL, {}, format="json")
        assert response.status_code == 400
        body = response.json()
        for required in ("equipment", "kind", "scheduled_date"):
            assert required in body


class TestScheduleList:
    def test_list_paginated(self, auth_client, equipment):
        MaintenanceScheduleFactory.create_batch(3, equipment=equipment)

        response = auth_client.get(LIST_URL)

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3
        assert "results" in body

    def test_filter_by_equipment(self, auth_client, branch):
        eq1 = EquipmentFactory(branch=branch)
        eq2 = EquipmentFactory(branch=branch)
        MaintenanceScheduleFactory.create_batch(2, equipment=eq1)
        MaintenanceScheduleFactory(equipment=eq2)

        response = auth_client.get(LIST_URL, {"equipment": eq1.id})

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_filter_by_branch(self, auth_client):
        from apps.branches.tests.factories import BranchFactory

        b1 = BranchFactory()
        b2 = BranchFactory()
        eq1 = EquipmentFactory(branch=b1)
        eq2 = EquipmentFactory(branch=b2)
        MaintenanceScheduleFactory.create_batch(2, equipment=eq1)
        MaintenanceScheduleFactory(equipment=eq2)

        response = auth_client.get(LIST_URL, {"branch": b1.id})

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_filter_by_kind(self, auth_client, equipment):
        MaintenanceScheduleFactory(
            equipment=equipment, kind=ScheduledMaintenanceKind.PREVENTIVE
        )
        MaintenanceScheduleFactory(
            equipment=equipment, kind=ScheduledMaintenanceKind.REPAIR
        )

        response = auth_client.get(LIST_URL, {"kind": "REPAIR"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_filter_by_is_completed(self, auth_client, equipment):
        MaintenanceScheduleFactory(equipment=equipment, is_completed=False)
        MaintenanceScheduleFactory(equipment=equipment, is_completed=True)

        response = auth_client.get(LIST_URL, {"is_completed": "true"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_filter_by_scheduled_date_range(self, auth_client, equipment):
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=date(2026, 5, 1)
        )
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=date(2026, 6, 15)
        )
        MaintenanceScheduleFactory(
            equipment=equipment, scheduled_date=date(2026, 12, 1)
        )

        response = auth_client.get(
            LIST_URL,
            {
                "scheduled_date_after": "2026-05-01",
                "scheduled_date_before": "2026-06-30",
            },
        )

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_search_by_notes(self, auth_client, equipment):
        MaintenanceScheduleFactory(equipment=equipment, notes="Cambio de batería")
        MaintenanceScheduleFactory(equipment=equipment, notes="Calibración general")

        response = auth_client.get(LIST_URL, {"search": "batería"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_search_by_asset_tag(self, auth_client, branch):
        target = EquipmentFactory(asset_tag="SCH-TARGET", branch=branch)
        other = EquipmentFactory(asset_tag="SCH-OTHER", branch=branch)
        MaintenanceScheduleFactory(equipment=target)
        MaintenanceScheduleFactory(equipment=other)

        response = auth_client.get(LIST_URL, {"search": "TARGET"})

        assert response.status_code == 200
        assert response.json()["count"] == 1


class TestScheduleRetrieve:
    def test_retrieve(self, auth_client, schedule):
        response = auth_client.get(detail_url(schedule.id))

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == schedule.id
        assert body["equipment_asset_tag"] == schedule.equipment.asset_tag

    def test_retrieve_missing_returns_404(self, auth_client):
        assert auth_client.get(detail_url(99999)).status_code == 404


class TestScheduleUpdate:
    def test_patch_partial(self, auth_client, schedule):
        response = auth_client.patch(
            detail_url(schedule.id), {"notes": "Notas nuevas"}, format="json"
        )
        assert response.status_code == 200
        schedule.refresh_from_db()
        assert schedule.notes == "Notas nuevas"

    def test_patch_allows_past_date_when_only_completing(self, auth_client, schedule):
        past = (date.today() - timedelta(days=2)).isoformat()
        response = auth_client.patch(
            detail_url(schedule.id),
            {"scheduled_date": past, "is_completed": True},
            format="json",
        )
        assert response.status_code == 200
        schedule.refresh_from_db()
        assert schedule.is_completed is True


class TestScheduleDelete:
    def test_delete(self, auth_client, schedule):
        response = auth_client.delete(detail_url(schedule.id))
        assert response.status_code == 204
        assert not MaintenanceSchedule.objects.filter(id=schedule.id).exists()


class TestCompleteAction:
    def test_complete_marks_is_completed(self, auth_client, schedule):
        assert schedule.is_completed is False
        response = auth_client.post(complete_url(schedule.id))
        assert response.status_code == 200
        assert response.json()["is_completed"] is True
        schedule.refresh_from_db()
        assert schedule.is_completed is True


class TestNotifyAction:
    @mock.patch("api.v1.scheduling.views.send_schedule_notification.delay")
    def test_notify_enqueues_task(self, mock_delay, auth_client, schedule):
        response = auth_client.post(notify_url(schedule.id))
        assert response.status_code == 200
        assert response.json() == {"detail": "notification_queued"}
        mock_delay.assert_called_once_with(schedule.pk)
