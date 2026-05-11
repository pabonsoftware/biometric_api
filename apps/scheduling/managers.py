from django.db import models


class MaintenanceScheduleQuerySet(models.QuerySet):
    def for_equipment(self, equipment_id: int) -> "MaintenanceScheduleQuerySet":
        return self.filter(equipment_id=equipment_id)

    def for_branch(self, branch_id: int) -> "MaintenanceScheduleQuerySet":
        return self.filter(equipment__branch_id=branch_id)

    def pending(self) -> "MaintenanceScheduleQuerySet":
        return self.filter(is_completed=False)

    def completed(self) -> "MaintenanceScheduleQuerySet":
        return self.filter(is_completed=True)

    def in_range(self, start, end) -> "MaintenanceScheduleQuerySet":
        return self.filter(scheduled_date__gte=start, scheduled_date__lte=end)

    def assigned_to_engineer(self, user_id: int) -> "MaintenanceScheduleQuerySet":
        return self.filter(assigned_engineer_id=user_id)

    def assigned_to_technician(self, user_id: int) -> "MaintenanceScheduleQuerySet":
        return self.filter(assigned_technician_id=user_id)

    def unassigned(self) -> "MaintenanceScheduleQuerySet":
        return self.filter(assigned_engineer__isnull=True, assigned_technician__isnull=True)


class MaintenanceScheduleManager(
    models.Manager.from_queryset(MaintenanceScheduleQuerySet)
):
    def get_queryset(self) -> MaintenanceScheduleQuerySet:
        return MaintenanceScheduleQuerySet(self.model, using=self._db).select_related(
            "equipment",
            "equipment__branch",
            "assigned_engineer",
            "assigned_technician",
        )
