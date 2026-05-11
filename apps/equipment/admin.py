from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Equipment


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "asset_tag",
        "equipment_model",
        "branch",
        "status",
        "risk_class",
        "created_at",
    )
    list_filter = ("status", "branch", "risk_class", "equipment_model__brand")
    search_fields = (
        "name",
        "asset_tag",
        "equipment_model__name",
        "equipment_model__brand__name",
    )
    ordering = ("name",)
    readonly_fields = ("qr_code", "created_at", "updated_at")
    autocomplete_fields = ("branch", "equipment_model")
    fieldsets = (
        (_("Identificación"), {"fields": ("name", "asset_tag", "equipment_model")}),
        (
            _("Ubicación y estado"),
            {"fields": ("branch", "location", "status", "risk_class", "purchase_date")},
        ),
        (_("Código QR"), {"fields": ("qr_code",)}),
        (_("Auditoría"), {"fields": ("created_at", "updated_at")}),
    )
