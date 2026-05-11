from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import MaintenanceSchedule


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "equipment",
        "kind",
        "scheduled_date",
        "assigned_engineer",
        "assigned_technician",
        "is_completed",
        "notified_at",
        "created_at",
    )
    list_filter = (
        "kind",
        "is_completed",
        "scheduled_date",
        "equipment__branch",
        "assigned_engineer",
        "assigned_technician",
    )
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
    ordering = ("scheduled_date",)
    autocomplete_fields = ("equipment", "assigned_engineer", "assigned_technician")
    readonly_fields = ("notified_at", "created_at", "updated_at")
    fieldsets = (
        (
            _("Información general"),
            {"fields": ("equipment", "kind", "scheduled_date", "notes", "is_completed")},
        ),
        (
            _("Asignación"),
            {"fields": ("assigned_engineer", "assigned_technician")},
        ),
        (
            _("Notificación"),
            {"fields": ("notified_at",)},
        ),
        (
            _("Auditoría"),
            {"fields": ("created_at", "updated_at")},
        ),
    )
