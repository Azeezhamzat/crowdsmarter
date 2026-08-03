"""Seed the proposed packaging tiers and backfill existing organisations.

Limits are deliberately generous (well above anything any existing
organisation or test fixture uses) so this backfill cannot retroactively
break an existing tenant. See ADR 0031.
"""

from django.db import migrations
from django.utils import timezone


PLANS = [
    {
        "key": "team",
        "name": "Team",
        "description": "For a single team running a handful of governed decisions at a time.",
        "trial_days": 14,
        "max_active_decisions": 25,
        "max_active_members": 15,
        "includes_advanced_foresight": True,
        "includes_ai_assistance": True,
        "support_level": "community",
        "order": 0,
    },
    {
        "key": "professional",
        "name": "Professional",
        "description": "For organisations running decision intelligence across multiple teams.",
        "trial_days": 14,
        "max_active_decisions": None,
        "max_active_members": 50,
        "includes_advanced_foresight": True,
        "includes_ai_assistance": True,
        "support_level": "standard",
        "order": 1,
    },
    {
        "key": "enterprise",
        "name": "Enterprise",
        "description": "For organisations needing unlimited scale and priority support.",
        "trial_days": 30,
        "max_active_decisions": None,
        "max_active_members": None,
        "includes_advanced_foresight": True,
        "includes_ai_assistance": True,
        "support_level": "priority",
        "order": 2,
    },
]


def seed_plans_and_backfill(apps, schema_editor):  # type: ignore[no-untyped-def]
    Plan = apps.get_model("billing", "Plan")
    Organisation = apps.get_model("organisations", "Organisation")
    OrganisationSubscription = apps.get_model("billing", "OrganisationSubscription")

    plans_by_key = {}
    for values in PLANS:
        plan, _ = Plan.objects.get_or_create(key=values["key"], defaults=values)
        plans_by_key[values["key"]] = plan
    default_plan = plans_by_key["team"]

    for organisation in Organisation.objects.filter(subscription__isnull=True):
        OrganisationSubscription.objects.create(
            organisation=organisation,
            plan=default_plan,
            status="active",
            started_at=timezone.now(),
            created_by=organisation.created_by,
        )


def remove_seeded_plans(apps, schema_editor):  # type: ignore[no-untyped-def]
    Plan = apps.get_model("billing", "Plan")
    OrganisationSubscription = apps.get_model("billing", "OrganisationSubscription")
    OrganisationSubscription.objects.filter(plan__key__in=[p["key"] for p in PLANS]).delete()
    Plan.objects.filter(key__in=[p["key"] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
        ("organisations", "0002_administration_and_membership_history"),
    ]

    operations = [
        migrations.RunPython(seed_plans_and_backfill, remove_seeded_plans),
    ]
