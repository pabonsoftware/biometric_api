from datetime import date, timedelta

import pytest
from django.core import mail

from apps.scheduling.models import MaintenanceSchedule, ScheduledMaintenanceKind
from apps.scheduling.tasks import send_schedule_notification

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
