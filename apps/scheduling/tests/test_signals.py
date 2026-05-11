from datetime import date, timedelta
from unittest import mock

import pytest

from apps.scheduling.models import MaintenanceSchedule, ScheduledMaintenanceKind

from .factories import MaintenanceScheduleFactory

pytestmark = pytest.mark.django_db


class TestScheduleNotificationSignal:
    @mock.patch("apps.scheduling.signals.send_schedule_notification.delay")
    def test_post_save_created_enqueues_task(self, mock_delay, equipment):
        schedule = MaintenanceSchedule.objects.create(
            equipment=equipment,
            kind=ScheduledMaintenanceKind.PREVENTIVE,
            scheduled_date=date.today() + timedelta(days=15),
        )

        mock_delay.assert_called_once_with(schedule.pk)

    @mock.patch("apps.scheduling.signals.send_schedule_notification.delay")
    def test_post_save_updated_does_not_enqueue(self, mock_delay, equipment):
        schedule = MaintenanceScheduleFactory(equipment=equipment)
        mock_delay.reset_mock()

        schedule.notes = "Notas actualizadas"
        schedule.save()

        mock_delay.assert_not_called()
