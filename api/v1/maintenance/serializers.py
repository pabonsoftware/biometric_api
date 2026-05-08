from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.maintenance.models import MaintenanceRecord
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
    # Representación anidada (read-only) + campo plano para escribir.
    assigned_engineer_detail = _AssignedUserSerializer(
        source="assigned_engineer", read_only=True
    )
    assigned_technician_detail = _AssignedUserSerializer(
        source="assigned_technician", read_only=True
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
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "pdf_file_url",
            "assigned_engineer_detail",
            "assigned_technician_detail",
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
        return super().update(instance, validated_data)
