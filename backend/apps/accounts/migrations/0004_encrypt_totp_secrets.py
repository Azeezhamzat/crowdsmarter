import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import migrations, models


def encrypt_existing_totp_secrets(apps, schema_editor):
    if not settings.MFA_ENCRYPTION_KEY:
        raise RuntimeError("MFA_ENCRYPTION_KEY is required before applying this migration.")
    digest = hashlib.sha256(settings.MFA_ENCRYPTION_KEY.encode("utf-8")).digest()
    fernet = Fernet(base64.urlsafe_b64encode(digest))
    TOTPDevice = apps.get_model("accounts", "TOTPDevice")
    for device in TOTPDevice.objects.all().iterator():
        device.secret_encrypted = fernet.encrypt(
            device.secret_encrypted.encode("utf-8")
        ).decode("utf-8")
        device.save(update_fields=["secret_encrypted"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_totpdevice_mfabackupcode")]

    operations = [
        migrations.RenameField(
            model_name="totpdevice",
            old_name="secret",
            new_name="secret_encrypted",
        ),
        migrations.AlterField(
            model_name="totpdevice",
            name="secret_encrypted",
            field=models.TextField(),
        ),
        migrations.RunPython(encrypt_existing_totp_secrets, migrations.RunPython.noop),
    ]
