# Generated manually for Phase 11.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("foresight", "0001_initial"),
        ("evidence", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="evidence",
            name="source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="decision_evidence",
                to="foresight.source",
            ),
        ),
    ]
