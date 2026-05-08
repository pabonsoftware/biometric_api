from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.scheduling.models import MaintenanceSchedule
from apps.scheduling.tasks import send_schedule_notification

from .filters import MaintenanceScheduleFilter
from .serializers import MaintenanceScheduleSerializer


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    """CRUD de agendamientos de mantenimiento + acciones complete/notify."""

    queryset = MaintenanceSchedule.objects.all()
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = MaintenanceScheduleFilter
    search_fields = (
        "notes",
        "equipment__asset_tag",
        "equipment__name",
        "assigned_engineer__username",
        "assigned_engineer__first_name",
        "assigned_engineer__last_name",
        "assigned_technician__username",
        "assigned_technician__first_name",
        "assigned_technician__last_name",
    )
    ordering_fields = ("scheduled_date", "created_at")
    ordering = ("scheduled_date",)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        schedule = self.get_object()
        schedule.is_completed = True
        schedule.save(update_fields=["is_completed", "updated_at"])
        return Response(self.get_serializer(schedule).data)

    @action(detail=True, methods=["post"], url_path="notify")
    def notify(self, request, pk=None):
        schedule = self.get_object()
        send_schedule_notification.delay(schedule.pk)
        return Response(
            {"detail": "notification_queued"}, status=status.HTTP_200_OK
        )
