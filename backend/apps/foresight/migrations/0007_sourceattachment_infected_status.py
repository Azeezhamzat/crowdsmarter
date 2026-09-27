from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("foresight", "0006_sourceattachment_malware_scan")]

    operations = [
        migrations.RemoveConstraint(
            model_name="sourceattachment",
            name="source_attachment_scan_status_valid",
        ),
        migrations.AlterField(
            model_name="sourceattachment",
            name="malware_scan_status",
            field=models.CharField(
                choices=[
                    ("not_scanned", "Not scanned"),
                    ("clean", "Clean"),
                    ("infected", "Infected"),
                    ("error", "Scan error"),
                ],
                default="not_scanned",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="sourceattachment",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "malware_scan_status__in",
                        ["not_scanned", "clean", "infected", "error"],
                    )
                ),
                name="source_attachment_scan_status_valid",
            ),
        ),
    ]
