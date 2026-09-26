import uuid

from django.db import migrations, models
import django.core.validators


def populate_idempotency_keys(apps, schema_editor):
    Disbursement = apps.get_model("disbursements", "Disbursement")
    for disbursement in Disbursement.objects.filter(idempotency_key__isnull=True).iterator():
        disbursement.idempotency_key = uuid.uuid4()
        disbursement.save(update_fields=["idempotency_key"])


class Migration(migrations.Migration):
    dependencies = [("disbursements", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="organisationdisbursementconfiguration",
            name="currency",
            field=models.CharField(
                default="USD",
                max_length=3,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Z]{3}$", "Use a three-letter ISO 4217 currency code."
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="disbursement",
            name="currency",
            field=models.CharField(
                default="USD",
                max_length=3,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Z]{3}$", "Use a three-letter ISO 4217 currency code."
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="disbursement",
            name="idempotency_key",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="disbursement",
            name="provider_detail",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="disbursement",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(populate_idempotency_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="disbursement",
            name="idempotency_key",
            field=models.UUIDField(editable=False, unique=True),
        ),
    ]
