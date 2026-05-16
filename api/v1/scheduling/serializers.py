from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.equipment.models import EquipmentStatus
from apps.maintenance.models import MaintenanceRecord
from apps.scheduling.models import MaintenanceSchedule
from apps.users.models import User


class _AssignedUserSerializer(serializers.ModelSerializer):
    """Representación mínima del usuario asignado (read-only, anidada)."""

    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "role", "role_display")

    def get_full_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class _MaintenanceRecordMiniSerializer(serializers.ModelSerializer):
    """Representación mínima del mantenimiento que cumplió un agendamiento."""

    class Meta:
        model = MaintenanceRecord
        fields = ("id", "kind", "date", "description", "cost")


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    equipment_asset_tag = serializers.CharField(source="equipment.asset_tag", read_only=True)
    branch_name = serializers.CharField(source="equipment.branch.name", read_only=True)
    assigned_engineer_detail = _AssignedUserSerializer(
        source="assigned_engineer", read_only=True
    )
    assigned_technician_detail = _AssignedUserSerializer(
        source="assigned_technician", read_only=True
    )
    maintenance_record = serializers.SerializerMethodField()
    maintenance_record_detail = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = (
            "id",
            "equipment",
            "equipment_asset_tag",
            "branch_name",
            "kind",
            "scheduled_date",
            "notes",
            "assigned_engineer",
            "assigned_engineer_detail",
            "assigned_technician",
            "assigned_technician_detail",
            "notified_at",
            "is_completed",
            "maintenance_record",
            "maintenance_record_detail",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "equipment_asset_tag",
            "branch_name",
            "assigned_engineer_detail",
            "assigned_technician_detail",
            "notified_at",
            "maintenance_record",
            "maintenance_record_detail",
            "created_at",
            "updated_at",
        )

    def _record(self, obj):
        # Acceso seguro al reverso OneToOne: si no hay vínculo, devuelve None
        # en lugar de levantar RelatedObjectDoesNotExist.
        return getattr(obj, "maintenance_record", None)

    def get_maintenance_record(self, obj):
        record = self._record(obj)
        return record.id if record is not None else None

    def get_maintenance_record_detail(self, obj):
        record = self._record(obj)
        if record is None:
            return None
        return _MaintenanceRecordMiniSerializer(record, context=self.context).data

    def validate_equipment(self, value):
        if value.status == EquipmentStatus.INACTIVE:
            raise serializers.ValidationError(
                _("El equipo no está disponible para programación.")
            )
        return value

    def validate_scheduled_date(self, value):
        if self.instance is None and value < timezone.localdate():
            raise serializers.ValidationError(
                _("La fecha programada no puede ser pasada.")
            )
        return value

    def validate_notes(self, value):
        return value.strip() if value else value

    def validate_assigned_engineer(self, value):
        if value is None:
            return value
        if not value.is_active:
            raise serializers.ValidationError(
                _("El usuario asignado no está activo.")
            )
        if value.role != User.Role.INGENIERO:
            raise serializers.ValidationError(
                _("El usuario asignado debe tener el rol de ingeniero biomédico.")
            )
        return value

    def validate_assigned_technician(self, value):
        if value is None:
            return value
        if not value.is_active:
            raise serializers.ValidationError(
                _("El usuario asignado no está activo.")
            )
        if value.role != User.Role.TECNICO:
            raise serializers.ValidationError(
                _("El usuario asignado debe tener el rol de técnico.")
            )
        return value
