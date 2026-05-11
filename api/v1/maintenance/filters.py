from django_filters import rest_framework as filters

from apps.maintenance.models import MaintenanceRecord


class MaintenanceRecordFilter(filters.FilterSet):
    equipment = filters.NumberFilter(field_name="equipment_id")
    branch = filters.NumberFilter(field_name="equipment__branch_id")
    kind = filters.CharFilter(field_name="kind", lookup_expr="iexact")
    date_after = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateFilter(field_name="date", lookup_expr="lte")
    assigned_engineer = filters.NumberFilter(field_name="assigned_engineer_id")
    assigned_technician = filters.NumberFilter(field_name="assigned_technician_id")
    unassigned = filters.BooleanFilter(method="filter_unassigned")

    class Meta:
        model = MaintenanceRecord
        fields = (
            "equipment",
            "branch",
            "kind",
            "date_after",
            "date_before",
            "assigned_engineer",
            "assigned_technician",
            "unassigned",
        )

    def filter_unassigned(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                assigned_engineer__isnull=True, assigned_technician__isnull=True
            )
        if value is False:
            return queryset.exclude(
                assigned_engineer__isnull=True, assigned_technician__isnull=True
            )
        return queryset
