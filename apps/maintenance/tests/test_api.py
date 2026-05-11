from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.equipment.tests.factories import EquipmentFactory
from apps.maintenance.models import MaintenanceKind, MaintenanceRecord

from .factories import MaintenanceRecordFactory

pytestmark = pytest.mark.django_db


LIST_URL = reverse("v1:maintenance:record-list")


def detail_url(pk: int) -> str:
    return reverse("v1:maintenance:record-detail", args=[pk])


def history_url(pk: int) -> str:
    return reverse("v1:equipment:equipment-history", args=[pk])


class TestMaintenanceAuth:
    def test_list_requires_auth(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401

    def test_create_requires_auth(self, api_client, equipment):
        payload = {
            "equipment": equipment.id,
            "kind": MaintenanceKind.PREVENTIVE,
            "date": "2026-01-01",
            "description": "x",
        }
        assert api_client.post(LIST_URL, payload, format="json").status_code == 401


class TestMaintenanceCreate:
    def _payload(self, equipment, **overrides):
        data = {
            "equipment": equipment.id,
            "kind": MaintenanceKind.PREVENTIVE,
            "date": "2026-01-15",
            "description": "Limpieza general y calibración trimestral.",
            "technician": "Juan Perez",
            "cost": "150000.00",
        }
        data.update(overrides)
        return data

    def test_create_without_pdf_returns_201(self, auth_client, equipment):
        response = auth_client.post(LIST_URL, self._payload(equipment), format="json")

        assert response.status_code == 201
        body = response.json()
        assert body["equipment"] == equipment.id
        assert body["equipment_asset_tag"] == equipment.asset_tag
        assert body["pdf_file"] in (None, "")
        assert body["pdf_file_url"] is None
        assert MaintenanceRecord.objects.count() == 1

    def test_create_strips_description(self, auth_client, equipment):
        response = auth_client.post(
            LIST_URL,
            self._payload(equipment, description="   Mantenimiento OK   "),
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == "Mantenimiento OK"

    def test_create_with_future_date_returns_400(self, auth_client, equipment):
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        response = auth_client.post(LIST_URL, self._payload(equipment, date=future), format="json")
        assert response.status_code == 400
        assert "La fecha no puede ser futura." in response.json()["date"][0]

    def test_create_with_empty_description_returns_400(self, auth_client, equipment):
        response = auth_client.post(
            LIST_URL, self._payload(equipment, description="   "), format="json"
        )
        assert response.status_code == 400
        assert "La descripción es obligatoria." in response.json()["description"][0]

    def test_create_with_negative_cost_returns_400(self, auth_client, equipment):
        response = auth_client.post(LIST_URL, self._payload(equipment, cost="-1.00"), format="json")
        assert response.status_code == 400
        assert "El costo no puede ser negativo." in response.json()["cost"][0]

    def test_create_missing_required_fields_returns_400(self, auth_client):
        response = auth_client.post(LIST_URL, {}, format="json")
        assert response.status_code == 400
        body = response.json()
        for required in ("equipment", "kind", "date", "description"):
            assert required in body


class TestMaintenanceList:
    def test_list_paginated(self, auth_client, equipment):
        MaintenanceRecordFactory.create_batch(3, equipment=equipment)

        response = auth_client.get(LIST_URL)

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3
        assert "results" in body

    def test_filter_by_equipment(self, auth_client, branch):
        eq1 = EquipmentFactory(branch=branch)
        eq2 = EquipmentFactory(branch=branch)
        MaintenanceRecordFactory.create_batch(2, equipment=eq1)
        MaintenanceRecordFactory(equipment=eq2)

        response = auth_client.get(LIST_URL, {"equipment": eq1.id})

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_filter_by_kind(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, kind=MaintenanceKind.PREVENTIVE)
        MaintenanceRecordFactory(equipment=equipment, kind=MaintenanceKind.CORRECTIVE)
        MaintenanceRecordFactory(equipment=equipment, kind=MaintenanceKind.REPAIR)

        response = auth_client.get(LIST_URL, {"kind": "CORRECTIVE"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_filter_by_date_range(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 1, 1))
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 6, 15))
        MaintenanceRecordFactory(equipment=equipment, date=date(2026, 1, 1))

        response = auth_client.get(
            LIST_URL,
            {"date_after": "2025-01-01", "date_before": "2025-12-31"},
        )

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_filter_by_branch(self, auth_client):
        from apps.branches.tests.factories import BranchFactory

        b1 = BranchFactory()
        b2 = BranchFactory()
        eq1 = EquipmentFactory(branch=b1)
        eq2 = EquipmentFactory(branch=b2)
        MaintenanceRecordFactory.create_batch(2, equipment=eq1)
        MaintenanceRecordFactory(equipment=eq2)

        response = auth_client.get(LIST_URL, {"branch": b1.id})

        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_search_by_description(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, description="Cambio de batería")
        MaintenanceRecordFactory(equipment=equipment, description="Calibración general")

        response = auth_client.get(LIST_URL, {"search": "batería"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_search_by_technician(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, technician="Maria Lopez")
        MaintenanceRecordFactory(equipment=equipment, technician="Juan Perez")

        response = auth_client.get(LIST_URL, {"search": "Maria"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_search_by_equipment_asset_tag(self, auth_client, branch):
        eq_target = EquipmentFactory(asset_tag="EQ-TARGET", branch=branch)
        eq_other = EquipmentFactory(asset_tag="EQ-OTHER", branch=branch)
        MaintenanceRecordFactory(equipment=eq_target)
        MaintenanceRecordFactory(equipment=eq_other)

        response = auth_client.get(LIST_URL, {"search": "TARGET"})

        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_default_ordering_desc_by_date(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 1, 1))
        MaintenanceRecordFactory(equipment=equipment, date=date(2026, 1, 1))
        MaintenanceRecordFactory(equipment=equipment, date=date(2025, 6, 15))

        response = auth_client.get(LIST_URL)

        dates = [item["date"] for item in response.json()["results"]]
        assert dates == sorted(dates, reverse=True)

    def test_ordering_by_cost_asc(self, auth_client, equipment):
        MaintenanceRecordFactory(equipment=equipment, cost=300)
        MaintenanceRecordFactory(equipment=equipment, cost=100)
        MaintenanceRecordFactory(equipment=equipment, cost=200)

        response = auth_client.get(LIST_URL, {"ordering": "cost"})

        costs = [float(item["cost"]) for item in response.json()["results"]]
        assert costs == sorted(costs)


class TestMaintenanceRetrieve:
    def test_retrieve_record(self, auth_client, maintenance_record):
        response = auth_client.get(detail_url(maintenance_record.id))

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == maintenance_record.id
        assert body["equipment_asset_tag"] == maintenance_record.equipment.asset_tag

    def test_retrieve_missing_returns_404(self, auth_client):
        assert auth_client.get(detail_url(99999)).status_code == 404


class TestMaintenanceUpdate:
    def test_patch_partial_update(self, auth_client, maintenance_record):
        response = auth_client.patch(
            detail_url(maintenance_record.id),
            {"description": "Descripción actualizada"},
            format="json",
        )

        assert response.status_code == 200
        maintenance_record.refresh_from_db()
        assert maintenance_record.description == "Descripción actualizada"

    def test_put_replaces_all_fields(self, auth_client, maintenance_record):
        payload = {
            "equipment": maintenance_record.equipment.id,
            "kind": MaintenanceKind.CORRECTIVE,
            "date": "2026-02-01",
            "description": "Reemplazo total del registro",
            "technician": "Nuevo Técnico",
            "cost": "999.00",
        }
        response = auth_client.put(detail_url(maintenance_record.id), payload, format="json")

        assert response.status_code == 200
        maintenance_record.refresh_from_db()
        assert maintenance_record.kind == MaintenanceKind.CORRECTIVE
        assert maintenance_record.technician == "Nuevo Técnico"

    def test_patch_with_future_date_returns_400(self, auth_client, maintenance_record):
        future = (timezone.localdate() + timedelta(days=10)).isoformat()
        response = auth_client.patch(
            detail_url(maintenance_record.id), {"date": future}, format="json"
        )
        assert response.status_code == 400
        assert "La fecha no puede ser futura." in response.json()["date"][0]


class TestMaintenanceDelete:
    def test_delete_record(self, auth_client, maintenance_record):
        response = auth_client.delete(detail_url(maintenance_record.id))

        assert response.status_code == 204
        assert not MaintenanceRecord.objects.filter(id=maintenance_record.id).exists()

    def test_delete_missing_returns_404(self, auth_client):
        assert auth_client.delete(detail_url(99999)).status_code == 404


class TestEquipmentHistoryAction:
    def test_history_returns_only_records_of_equipment(self, auth_client, branch):
        target = EquipmentFactory(branch=branch)
        other = EquipmentFactory(branch=branch)
        MaintenanceRecordFactory.create_batch(3, equipment=target)
        MaintenanceRecordFactory(equipment=other)

        response = auth_client.get(history_url(target.id))

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 3
        for item in body["results"]:
            assert item["equipment"] == target.id

    def test_history_paginated_response(self, auth_client, equipment):
        MaintenanceRecordFactory.create_batch(2, equipment=equipment)

        response = auth_client.get(history_url(equipment.id))

        assert response.status_code == 200
        body = response.json()
        assert "results" in body
        assert "count" in body

    def test_history_returns_404_for_unknown_equipment(self, auth_client):
        assert auth_client.get(history_url(99999)).status_code == 404

    def test_history_requires_auth(self, api_client, equipment):
        assert api_client.get(history_url(equipment.id)).status_code == 401
