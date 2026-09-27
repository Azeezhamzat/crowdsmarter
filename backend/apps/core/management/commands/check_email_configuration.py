"""Validate email delivery configuration without sending a message."""

from django.conf import settings
from django.core.checks import run_checks
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Validate provider-ready email settings without sending external email."

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        email_check_ids = {
            "crowdsmarter.E001",
            "crowdsmarter.E002",
            "crowdsmarter.E003",
            "crowdsmarter.E004",
        }
        errors = [
            item
            for item in run_checks(tags=["security"], include_deployment_checks=True)
            if item.id in email_check_ids
        ]
        if errors:
            raise CommandError("; ".join(str(item.msg) for item in errors))
        self.stdout.write(
            self.style.SUCCESS(
                "Email configuration is internally consistent: "
                f"backend={settings.EMAIL_BACKEND}, from={settings.DEFAULT_FROM_EMAIL}."
            )
        )
