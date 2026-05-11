from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.failures.models import FailureRecord


class FailureRecordSerializer(serializers.ModelSerializer):
    equipment_asset_tag = serializers.CharField(source="equipment.asset_tag", read_only=True)
    branch_name = serializers.CharField(source="equipment.branch.name", read_only=True)
    # Sin trim_whitespace para que un valor "   " caiga en validate_description
    # y dispare el mensaje en español, en lugar del genérico de DRF.
    description = serializers.CharField(trim_whitespace=False)

    class Meta:
        model = FailureRecord
        fields = (
            "id",
            "equipment",
            "equipment_asset_tag",
            "branch_name",
            "reported_at",
            "description",
            "severity",
            "resolved",
            "resolved_at",
            "resolution_notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_description(self, value: str) -> str:
        normalized = value.strip() if value else ""
        if not normalized:
            raise serializers.ValidationError(_("La descripción es obligatoria."))
        return normalized

    def validate_resolution_notes(self, value: str) -> str:
        return value.strip() if value else ""

    def validate_reported_at(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError(_("La fecha de reporte no puede ser futura."))
        return value

    def validate(self, attrs):
        instance = self.instance
        resolved = attrs.get("resolved", getattr(instance, "resolved", False))
        # Distingue "no enviado" de "enviado como null" para validación cruzada.
        resolved_at_in_payload = "resolved_at" in attrs
        resolved_at = attrs.get("resolved_at", getattr(instance, "resolved_at", None))
        reported_at = attrs.get("reported_at", getattr(instance, "reported_at", None))

        if resolved and resolved_at is None:
            attrs["resolved_at"] = timezone.now()
            resolved_at = attrs["resolved_at"]

        if not resolved and resolved_at is not None:
            # Solo error si el cliente envió `resolved_at` explícitamente; si la
            # instancia ya lo traía, simplemente lo limpiamos al "des-resolver".
            if resolved_at_in_payload:
                raise serializers.ValidationError(
                    {
                        "resolved_at": _(
                            "No se puede definir 'resuelta el' sin marcar la falla como"
                            " resuelta."
                        )
                    }
                )
            attrs["resolved_at"] = None
            resolved_at = None

        if resolved_at and reported_at and resolved_at < reported_at:
            raise serializers.ValidationError(
                {"resolved_at": _("La fecha de resolución no puede ser anterior al reporte.")}
            )
        return attrs


class ResolveFailureSerializer(serializers.Serializer):
    """Body opcional del endpoint POST /failures/{id}/resolve/."""

    resolution_notes = serializers.CharField(required=False, allow_blank=True)
