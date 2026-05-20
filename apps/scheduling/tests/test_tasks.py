from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail

from apps.notifications.consumers import (
    STAFF_SUPERVISOR_GROUP,
    user_group_name,
)
from apps.scheduling.models import MaintenanceSchedule, ScheduledMaintenanceKind
from apps.scheduling.tasks import send_schedule_notification
from apps.users.tests.factories import IngenieroFactory, TecnicoFactory

from .factories import MaintenanceScheduleFactory

pytestmark = pytest.mark.django_db


class TestSendScheduleNotification:
    def test_sends_email_to_configured_recipients(self, settings, equipment):
        # Sin email de sede para validar exclusivamente la lista CSV.
        equipment.branch.email = ""
        equipment.branch.save(update_fields=["email"])
        schedule = MaintenanceScheduleFactory(
            equipment=equipment,
            kind=ScheduledMaintenanceKind.PREVENTIVE,
            scheduled_date=date.today() + timedelta(days=20),
        )
        # post_save signal already sent the email via eager mode; reset and re-trigger.
        mail.outbox = []

        result = send_schedule_notification(schedule.pk)

        assert result == "sent"
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert equipment.asset_tag in message.subject
        assert schedule.scheduled_date.isoformat() in message.subject
        assert set(message.to) == set(settings.MAINTENANCE_NOTIFICATION_EMAILS)
        assert equipment.name in message.body
        assert equipment.branch.name in message.body
        # HTML alternative is attached
        html_alt = next((alt for alt in message.alternatives if alt[1] == "text/html"), None)
        assert html_alt is not None
        assert equipment.asset_tag in html_alt[0]

    def test_sets_notified_at_after_send(self, equipment):
        schedule = MaintenanceScheduleFactory(equipment=equipment)
        # Eager mode already filled notified_at via signal — re-running is idempotent
        send_schedule_notification(schedule.pk)
        schedule.refresh_from_db()
        assert schedule.notified_at is not None

    def test_includes_branch_email_when_present(self, settings, branch, equipment):
        branch.email = "branch@clinic.test"
        branch.save(update_fields=["email"])
        schedule = MaintenanceScheduleFactory(equipment=equipment)
        mail.outbox = []

        send_schedule_notification(schedule.pk)

        recipients = set(mail.outbox[0].to)
        assert "branch@clinic.test" in recipients
        assert "mantenimiento@clinic.test" in recipients

    def test_includes_assigned_engineer_and_technician_emails(self, equipment):
        engineer = IngenieroFactory(email="ingeniero@clinic.test")
        technician = TecnicoFactory(email="tecnico@clinic.test")
        schedule = MaintenanceScheduleFactory(
            equipment=equipment,
            assigned_engineer=engineer,
            assigned_technician=technician,
        )
        mail.outbox = []

        send_schedule_notification(schedule.pk)

        recipients = set(mail.outbox[0].to)
        assert "ingeniero@clinic.test" in recipients
        assert "tecnico@clinic.test" in recipients

    def test_returns_no_recipients_when_empty(self, settings, equipment):
        settings.MAINTENANCE_NOTIFICATION_EMAILS = []
        # equipment.branch.email is empty by default in BranchFactory? Force empty.
        equipment.branch.email = ""
        equipment.branch.save(update_fields=["email"])
        schedule = MaintenanceScheduleFactory(equipment=equipment)
        mail.outbox = []

        result = send_schedule_notification(schedule.pk)

        assert result == "no_recipients"
        assert mail.outbox == []

    def test_returns_not_found_for_missing_schedule(self):
        result = send_schedule_notification(99999)
        assert result == "schedule_not_found"
        assert MaintenanceSchedule.objects.count() == 0


class TestScheduleNotificationBroadcast:
    """El push WS debe alcanzar al ingeniero, al técnico y al grupo de supervisión."""

    def _capture_group_sends(self, equipment, engineer=None, technician=None):
        schedule = MaintenanceScheduleFactory(
            equipment=equipment,
            assigned_engineer=engineer,
            assigned_technician=technician,
        )
        mail.outbox = []

        fake_layer = MagicMock()

        async def fake_group_send(group, message):  # noqa: ANN001
            fake_layer.calls.append((group, message))

        fake_layer.calls = []
        fake_layer.group_send = fake_group_send

        with patch(
            "apps.scheduling.tasks.get_channel_layer", return_value=fake_layer
        ):
            send_schedule_notification(schedule.pk)

        return schedule, fake_layer.calls

    def test_broadcasts_to_engineer_technician_and_supervisors(self, equipment):
        engineer = IngenieroFactory()
        technician = TecnicoFactory()
        _, calls = self._capture_group_sends(equipment, engineer, technician)

        groups = [group for group, _msg in calls]
        assert user_group_name(engineer.pk) in groups
        assert user_group_name(technician.pk) in groups
        assert STAFF_SUPERVISOR_GROUP in groups
        assert len(calls) == 3

    def test_skips_assignment_groups_when_unassigned(self, equipment):
        _, calls = self._capture_group_sends(equipment)
        groups = [group for group, _msg in calls]
        # Sólo el broadcast — no hay user.<pk> de nadie.
        assert groups == [STAFF_SUPERVISOR_GROUP]

    def test_payload_carries_schedule_metadata(self, equipment):
        engineer = IngenieroFactory()
        schedule, calls = self._capture_group_sends(equipment, engineer)

        _, message = calls[0]
        assert message["type"] == "notification.message"
        payload = message["payload"]
        assert payload["type"] == "schedule_email_sent"
        assert payload["schedule_id"] == schedule.pk
        assert payload["equipment_asset_tag"] == equipment.asset_tag
        assert payload["scheduled_date"] == schedule.scheduled_date.isoformat()
        assert payload["branch_name"] == equipment.branch.name

    def test_skips_broadcast_when_channel_layer_unavailable(self, equipment):
        """Si no hay channel layer (entorno sin Redis), el correo sigue siendo
        el camino crítico — no debe lanzar ni dejar la task en estado fallido."""
        schedule = MaintenanceScheduleFactory(equipment=equipment)
        mail.outbox = []

        with patch("apps.scheduling.tasks.get_channel_layer", return_value=None):
            result = send_schedule_notification(schedule.pk)

        assert result == "sent"
