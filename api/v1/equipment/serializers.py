from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.branches.models import Branch
from apps.catalog.models import EquipmentModel
from apps.equipment.models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    equipment_model_name = serializers.CharField(source="equipment_model.name", read_only=True)
    brand_name = serializers.CharField(source="equipment_model.brand.name", read_only=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = (
            "id",
            "name",
            "asset_tag",
            "equipment_model",
            "equipment_model_name",
            "brand_name",
            "branch",
            "branch_name",
            "location",
            "purchase_date",
            "status",
            "risk_class",
            "qr_code",
            "qr_code_url",
            "mtbf_hours",
            "mttr_hours",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "equipment_model_name",
            "brand_name",
            "qr_code",
            "qr_code_url",
            "mtbf_hours",
            "mttr_hours",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            # El mensaje de unicidad lo controla validate_asset_tag (en español).
            "asset_tag": {"validators": []},
            "risk_class": {"required": False, "allow_null": True},
        }

    def get_qr_code_url(self, obj: Equipment) -> str | None:
        if not obj.qr_code:
            return None
        request = self.context.get("request")
        url = obj.qr_code.url
        return request.build_absolute_uri(url) if request else url

    def validate_asset_tag(self, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise serializers.ValidationError(_("El código de inventario no puede estar vacío."))
        qs = Equipment.objects.filter(asset_tag__iexact=normalized)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                _("Ya existe un equipo con este código de inventario.")
            )
        return normalized

    def validate_name(self, value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if not normalized:
            raise serializers.ValidationError(_("El nombre no puede estar vacío."))
        return normalized

    def validate_location(self, value: str) -> str:
        return value.strip()

    def validate_branch(self, value: Branch) -> Branch:
        if not value.is_active:
            raise serializers.ValidationError(_("La sede seleccionada no está activa."))
        return value

    def validate_equipment_model(self, value: EquipmentModel) -> EquipmentModel:
        if not value.is_active:
            raise serializers.ValidationError(_("El modelo seleccionado no está activo."))
        if not value.brand.is_active:
            raise serializers.ValidationError(_("La marca del modelo seleccionado no está activa."))
        return value

    def validate_purchase_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError(_("La fecha de compra no puede ser futura."))
        return value
