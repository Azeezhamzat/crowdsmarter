from django.db import migrations


SIMULATED_SLUGS = (
    "northstar-grid-services-sim",
    "careweave-regional-health-sim",
    "terrafood-futures-institute-sim",
)


def bootstrap(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    PlatformAdministrator = apps.get_model("platform_admin", "PlatformAdministrator")
    PlatformConfiguration = apps.get_model("platform_admin", "PlatformConfiguration")
    Organisation = apps.get_model("organisations", "Organisation")
    Membership = apps.get_model("organisations", "Membership")

    PlatformConfiguration.objects.get_or_create(
        singleton_key=1,
        defaults={
            "public_contact_email": "hello@crowdsmarter.com",
            "demo_email": "hello@crowdsmarter.com",
            "support_email": "hello@crowdsmarter.com",
            "privacy_email": "hello@crowdsmarter.com",
            "security_email": "hello@crowdsmarter.com",
            "notification_sender_email": "hello@crowdsmarter.com",
            "support_access_max_hours": 8,
        },
    )

    administrators = list(User.objects.filter(is_active=True, is_superuser=True).order_by("email"))
    for user in administrators:
        PlatformAdministrator.objects.get_or_create(
            user=user,
            defaults={
                "status": "active",
                "rationale": "Bootstrapped from an existing active Django superuser during Phase 18B migration.",
            },
        )

    simulated_organisations = Organisation.objects.filter(slug__in=SIMULATED_SLUGS)
    for user in administrators:
        for organisation in simulated_organisations:
            Membership.objects.update_or_create(
                organisation=organisation,
                user=user,
                defaults={"role": "owner", "status": "active"},
            )


def reverse_bootstrap(apps, schema_editor):
    # Capability and configuration records are intentionally preserved on reverse migration.
    pass


class Migration(migrations.Migration):
    dependencies = [("platform_admin", "0001_initial")]

    operations = [migrations.RunPython(bootstrap, reverse_bootstrap)]
