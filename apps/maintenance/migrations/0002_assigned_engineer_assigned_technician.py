import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("maintenance", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerecord",
            name="assigned_engineer",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"is_active": True, "role": "ingeniero"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="engineering_records",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ingeniero asignado",
            ),
        ),
        migrations.AddField(
            model_name="maintenancerecord",
            name="assigned_technician",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"is_active": True, "role": "tecnico"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="technician_records",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Técnico asignado",
            ),
        ),
        migrations.AddIndex(
            model_name="maintenancerecord",
            index=models.Index(fields=["assigned_engineer"], name="maint_engineer_idx"),
        ),
        migrations.AddIndex(
            model_name="maintenancerecord",
            index=models.Index(fields=["assigned_technician"], name="maint_technician_idx"),
        ),
    ]
