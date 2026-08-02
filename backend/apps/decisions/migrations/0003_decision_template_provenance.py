from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("decisions", "0002_decisionfinalisation")]

    operations = [
        migrations.AddField(
            model_name="decision",
            name="source_template_key",
            field=models.CharField(blank=True, default="", max_length=80),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="decision",
            name="source_template_version",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
