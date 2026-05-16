"""Endpoint agregado para el dashboard de la SPA.

Una sola request, una sola response. Las queries se aíslan en funciones helper para
testearlas independientemente del view.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.equipment.models import Equipment, EquipmentStatus
from apps.failures.models import FailureRecord, FailureSeverity
from apps.maintenance.models import MaintenanceKind, MaintenanceRecord
from apps.scheduling.models import MaintenanceSchedule

_MAINTENANCE_KINDS = [
    MaintenanceKind.PREVENTIVE,
    MaintenanceKind.CORRECTIVE,
    MaintenanceKind.REPAIR,
]


def _equipment_kpis() -> dict:
    by_status = dict(
        Equipment.objects.values_list("status").annotate(count=Count("id"))
    )
    return {
        "active": by_status.get(EquipmentStatus.ACTIVE, 0),
        "in_maintenance": by_status.get(EquipmentStatus.IN_MAINTENANCE, 0),
        "in_repair": by_status.get(EquipmentStatus.IN_REPAIR, 0),
        "inactive": by_status.get(EquipmentStatus.INACTIVE, 0),
        "total": sum(by_status.values()),
    }


def _failures_kpis() -> dict:
    open_qs = FailureRecord.objects.filter(resolved=False)
    return {
        "critical_open": open_qs.filter(severity=FailureSeverity.CRITICAL).count(),
        "total_open": open_qs.count(),
    }


def _scheduling_kpis(today: date) -> dict:
    pending = MaintenanceSchedule.objects.filter(is_completed=False)
    return {
        "next_7_days": pending.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=today + timedelta(days=7),
        ).count(),
        "overdue": pending.filter(scheduled_date__lt=today).count(),
    }


def _maintenance_kpis(today: date) -> dict:
    month_qs = MaintenanceRecord.objects.filter(
        date__year=today.year, date__month=today.month
    )
    aggregate = month_qs.aggregate(
        count=Count("id"),
        cost=Coalesce(Sum("cost"), Decimal(0)),
    )
    return {
        "this_month_count": aggregate["count"],
        "this_month_cost": str(aggregate["cost"]),
    }


def _equipment_distribution() -> list[dict]:
    return [
        {"status": s, "count": Equipment.objects.filter(status=s).count()}
        for s in (
            EquipmentStatus.ACTIVE,
            EquipmentStatus.IN_MAINTENANCE,
            EquipmentStatus.IN_REPAIR,
            EquipmentStatus.INACTIVE,
        )
    ]


def _failures_distribution() -> list[dict]:
    rows = []
    for severity in (
        FailureSeverity.LOW,
        FailureSeverity.MEDIUM,
        FailureSeverity.HIGH,
        FailureSeverity.CRITICAL,
    ):
        qs = FailureRecord.objects.filter(severity=severity)
        rows.append(
            {
                "severity": severity,
                "open": qs.filter(resolved=False).count(),
                "resolved": qs.filter(resolved=True).count(),
            }
        )
    return rows


def _maintenance_time_series(today: date) -> list[dict]:
    # Construye una lista ordenada de los últimos 6 meses incluyendo el actual.
    months: list[date] = []
    cursor = today.replace(day=1)
    for _ in range(6):
        months.append(cursor)
        # Restar un mes manteniendo el día 1.
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    months.reverse()

    start = months[0]
    rows = (
        MaintenanceRecord.objects.filter(date__gte=start)
        .annotate(bucket=TruncMonth("date"))
        .values("bucket", "kind")
        .annotate(count=Count("id"), cost=Coalesce(Sum("cost"), Decimal(0)))
    )

    by_month: dict[str, dict] = {
        m.isoformat()[:7]: {
            "month": m.isoformat()[:7],
            "PREVENTIVE": 0,
            "CORRECTIVE": 0,
            "REPAIR": 0,
            "cost": Decimal(0),
        }
        for m in months
    }
    for row in rows:
        # TruncMonth sobre un DateField devuelve date; sobre DateTimeField devuelve datetime.
        bucket = row["bucket"]
        bucket_key = (bucket.date() if hasattr(bucket, "date") else bucket).isoformat()[:7]
        if bucket_key not in by_month:
            continue
        by_month[bucket_key][row["kind"]] = row["count"]
        by_month[bucket_key]["cost"] += row["cost"]

    result = []
    for m in months:
        item = by_month[m.isoformat()[:7]]
        item["cost"] = str(item["cost"])
        result.append(item)
    return result


def _overdue_schedules(today: date) -> list[dict]:
    qs = (
        MaintenanceSchedule.objects.filter(
            is_completed=False, scheduled_date__lt=today
        )
        .select_related("equipment")
        .order_by("scheduled_date")[:10]
    )
    return [
        {
            "id": s.id,
            "equipment_id": s.equipment_id,
            "equipment_name": s.equipment.name,
            "equipment_asset_tag": s.equipment.asset_tag,
            "scheduled_date": s.scheduled_date.isoformat(),
            "days_overdue": (today - s.scheduled_date).days,
            "kind": s.kind,
        }
        for s in qs
    ]


def _worst_mtbf() -> list[dict]:
    qs = (
        Equipment.objects.annotate(failures_count=Count("failures"))
        .filter(failures_count__gte=2, mtbf_hours__isnull=False)
        .select_related("branch")
        .order_by("mtbf_hours")[:5]
    )
    return [
        {
            "id": e.id,
            "name": e.name,
            "asset_tag": e.asset_tag,
            "branch_name": e.branch.name,
            "mtbf_hours": str(e.mtbf_hours),
            "failures_count": e.failures_count,
        }
        for e in qs
    ]


def _my_schedules(user, today: date) -> list[dict]:
    qs = (
        MaintenanceSchedule.objects.filter(
            is_completed=False,
            scheduled_date__gte=today,
            scheduled_date__lte=today + timedelta(days=7),
        )
        .filter(Q(assigned_technician=user) | Q(assigned_engineer=user))
        .select_related("equipment")
        .order_by("scheduled_date")[:10]
    )
    return [
        {
            "id": s.id,
            "equipment_id": s.equipment_id,
            "equipment_name": s.equipment.name,
            "equipment_asset_tag": s.equipment.asset_tag,
            "scheduled_date": s.scheduled_date.isoformat(),
            "kind": s.kind,
        }
        for s in qs
    ]


class DashboardSummaryView(APIView):
    """Snapshot agregado para el dashboard. Sin cache en v1."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        today = timezone.localdate()
        payload = {
            "kpis": {
                "equipment": _equipment_kpis(),
                "failures": _failures_kpis(),
                "scheduling": _scheduling_kpis(today),
                "maintenance": _maintenance_kpis(today),
            },
            "distributions": {
                "equipment_by_status": _equipment_distribution(),
                "failures_by_severity": _failures_distribution(),
            },
            "time_series": {
                "maintenance_by_month": _maintenance_time_series(today),
            },
            "lists": {
                "overdue_schedules": _overdue_schedules(today),
                "worst_mtbf": _worst_mtbf(),
            },
            "my_tasks": {
                "schedules": _my_schedules(request.user, today),
                # FailureRecord no tiene "assigned_to" en v1; se reserva la key
                # para futuro sin obligar al frontend a defenderse contra ausencia.
                "failures": [],
            },
        }
        return Response(payload)


__all__ = ["DashboardSummaryView"]
# Re-export helpers privados para los tests.
_HELPERS = (
    _equipment_kpis,
    _failures_kpis,
    _scheduling_kpis,
    _maintenance_kpis,
    _equipment_distribution,
    _failures_distribution,
    _maintenance_time_series,
    _overdue_schedules,
    _worst_mtbf,
    _my_schedules,
    _MAINTENANCE_KINDS,
)
