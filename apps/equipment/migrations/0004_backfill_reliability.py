"""Backfill de MTBF y MTTR para equipos con fallas existentes.

Se ejecuta una vez después de añadir las columnas. Idempotente: re-correrla deja los
valores tal como están.
"""

from django.db import migrations


def backfill_metrics(apps, schema_editor):
    # Import lazy: reliability.py opera sobre el modelo Equipment "real" (no el
    # histórico de la migración), lo cual está bien aquí porque el cálculo solo
    # lee FailureRecord y escribe campos existentes.
    from apps.equipment.models import Equipment
    from apps.equipment.reliability import recompute_for

    for equipment in Equipment.objects.iterator():
        recompute_for(equipment)


def noop_reverse(apps, schema_editor):
    # Reversa: limpiar a null sin perder filas.
    Equipment = apps.get_model("equipment", "Equipment")
    Equipment.objects.update(mtbf_hours=None, mttr_hours=None)


class Migration(migrations.Migration):
    dependencies = [
        ("equipment", "0003_equipment_mtbf_hours_equipment_mttr_hours"),
        ("failures", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_metrics, reverse_code=noop_reverse),
    ]
