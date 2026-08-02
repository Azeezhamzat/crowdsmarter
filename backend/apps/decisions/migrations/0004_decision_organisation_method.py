# Generated for CrowdSmarter Phase 17.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("methodology", "0001_initial"),
        ("decisions", "0003_decision_template_provenance"),
    ]

    operations = [
        migrations.AddField(
            model_name="decision",
            name="source_method_version",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="decisions", to="methodology.decisionmethodversion"),
        ),
    ]
