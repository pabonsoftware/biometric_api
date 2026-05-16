from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.maintenance.models import MaintenanceRecord
from apps.scheduling.models import MaintenanceSchedule
from apps.users.models import User

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


class _AssignedUserSerializer(serializers.ModelSerializer):
    """Representación mínima del usuario asignado (read-only, anidada)."""

    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "role", "role_display")

    def get_full_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class _ScheduledMaintenanceMiniSerializer(serializers.ModelSerializer):
    """Representación mínima del agendamiento (read-only, anidada en MaintenanceRecord)."""

    class Meta:
        model = MaintenanceSchedule
        fields = ("id", "kind", "scheduled_date", "notes", "is_completed")


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    equipment_asset_tag = serializers.CharField(source="equipment.asset_tag", read_only=True)
    pdf_file_url = serializers.SerializerMethodField()
    # Sin trim_whitespace: queremos que un valor como "   " llegue a validate_description
    # y dispare nuestro mensaje en español, en lugar del genérico de DRF.
    description = serializers.CharField(trim_whitespace=False)
    # Definimos el campo cost explícitamente para que el mensaje de "no negativo"
    # provenga de validate_cost (en español) y no del MinValueValidator del modelo.
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    # Sobrescribimos el campo para deshabilitar el UniqueValidator auto-generado
    # por el OneToOneField — el mensaje en español lo emite validate_scheduled_maintenance
    # ("El agendamiento ya fue cumplido."). El UNIQUE constraint a nivel DB queda
    # como red de seguridad.
    scheduled_maintenance = serializers.PrimaryKeyRelatedField(
        queryset=MaintenanceSchedule.objects.all(),
        required=False,
        allow_null=True,
        validators=[],
    )
    # Representación anidada (read-only) + campo plano para escribir.
    assigned_engineer_detail = _AssignedUserSerializer(
        source="assigned_engineer", read_only=True
    )
    assigned_technician_detail = _AssignedUserSerializer(
        source="assigned_technician", read_only=True
    )
    scheduled_maintenance_detail = _ScheduledMaintenanceMiniSerializer(
        source="scheduled_maintenance", read_only=True
    )

    class Meta:
        model = MaintenanceRecord
        fields = (
            "id",
            "equipment",
            "equipment_asset_tag",
            "kind",
            "date",
            "description",
            "technician",
            "assigned_engineer",
            "assigned_engineer_detail",
            "assigned_technician",
            "assigned_technician_detail",
            "cost",
            "pdf_file",
            "pdf_file_url",
            "scheduled_maintenance",
            "scheduled_maintenance_detail",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "pdf_file_url",
            "assigned_engineer_detail",
            "assigned_technician_detail",
            "scheduled_maintenance_detail",
            "created_at",
            "updated_at",
        )

    def get_pdf_file_url(self, obj: MaintenanceRecord) -> str | None:
        if not obj.pdf_file:
            return None
        request = self.context.get("request")
        url = obj.pdf_file.url
        return request.build_absolute_uri(url) if request else url

    def validate_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError(_("La fecha no puede ser futura."))
        return value

    def validate_description(self, value: str) -> str:
        normalized = value.strip() if value else ""
        if not normalized:
            raise serializers.ValidationError(_("La descripción es obligatoria."))
        return normalized

    def validate_technician(self, value: str) -> str:
        return value.strip() if value else ""

    def validate_cost(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(_("El costo no puede ser negativo."))
        return value

    def validate_pdf_file(self, value):
        if value and value.size > MAX_PDF_BYTES:
            raise serializers.ValidationError(_("El archivo no puede superar los 10 MB."))
        return value

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

    def validate_scheduled_maintenance(self, value):
        if value is None:
            return value
        # En update, permitir reenviar el mismo vínculo aunque is_completed sea True
        # (el agendamiento fue cerrado por este mismo registro).
        current = (
            getattr(self.instance, "scheduled_maintenance_id", None)
            if self.instance is not None
            else None
        )
        if value.is_completed and value.id != current:
            raise serializers.ValidationError(_("El agendamiento ya fue cumplido."))
        return value

    def validate(self, attrs):
        schedule = attrs.get("scheduled_maintenance", serializers.empty)
        equipment = attrs.get("equipment")
        # En update: si el campo no vino en el payload, usar el actual.
        if schedule is serializers.empty:
            schedule = (
                self.instance.scheduled_maintenance if self.instance is not None else None
            )
        if equipment is None and self.instance is not None:
            equipment = self.instance.equipment

        if schedule is not None and equipment is not None and schedule.equipment_id != equipment.id:
            raise serializers.ValidationError(
                {"scheduled_maintenance": _("El agendamiento corresponde a otro equipo.")}
            )

        # No permitir cambiar un vínculo ya existente por uno distinto.
        if (
            self.instance is not None
            and "scheduled_maintenance" in attrs
            and self.instance.scheduled_maintenance_id is not None
            and (schedule is None or schedule.id != self.instance.scheduled_maintenance_id)
        ):
            raise serializers.ValidationError(
                {
                    "scheduled_maintenance": _(
                        "No se puede cambiar el agendamiento de un mantenimiento existente."
                    )
                }
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        schedule = instance.scheduled_maintenance
        if schedule is not None and not schedule.is_completed:
            schedule.is_completed = True
            schedule.save(update_fields=["is_completed", "updated_at"])
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        new_pdf = validated_data.get("pdf_file", serializers.empty)
        # Solo borrar si llega un valor nuevo (no si está ausente del payload)
        # y el nuevo valor es un archivo distinto al existente.
        if (
            new_pdf is not serializers.empty
            and new_pdf
            and instance.pdf_file
            and instance.pdf_file != new_pdf
        ):
            instance.pdf_file.delete(save=False)
        previous_schedule_id = instance.scheduled_maintenance_id
        instance = super().update(instance, validated_data)
        # Si quedó un vínculo nuevo (no había uno antes), cerrar el agendamiento.
        schedule = instance.scheduled_maintenance
        if (
            schedule is not None
            and previous_schedule_id is None
            and not schedule.is_completed
        ):
            schedule.is_completed = True
            schedule.save(update_fields=["is_completed", "updated_at"])
        return instance
