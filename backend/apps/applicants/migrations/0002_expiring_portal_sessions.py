from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("applicants", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="applicantaccount",
            name="portal_token_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Previously issued tokens had no expiry or server-side logout semantics.
        # Invalidate them so every active session uses the hardened lifecycle.
        migrations.RunSQL(
            "UPDATE applicants_applicantaccount SET portal_token_digest = NULL",
            migrations.RunSQL.noop,
        ),
    ]
