from django.db import migrations


def create_default_workspaces(apps, schema_editor):  # type: ignore[no-untyped-def]
    Organisation = apps.get_model("organisations", "Organisation")
    Workspace = apps.get_model("workspaces", "Workspace")
    for organisation in Organisation.objects.all().iterator():
        Workspace.objects.get_or_create(
            organisation_id=organisation.id,
            is_default=True,
            defaults={
                "name": "Decisions",
                "slug": "decisions",
                "description": "The organisation's primary decision workspace.",
                "created_by_id": organisation.created_by_id,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("workspaces", "0001_initial")]

    operations = [
        migrations.RunPython(create_default_workspaces, migrations.RunPython.noop),
    ]
