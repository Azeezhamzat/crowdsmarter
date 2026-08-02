"""Create one secure local owner only when an installation has no active account."""

from __future__ import annotations

import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.organisations.models import Membership, Organisation
from apps.workspaces.models import Workspace

User = get_user_model()


class Command(BaseCommand):
    """Guarantee first-run local access without introducing production defaults."""

    help = "Create a local owner and starter organisation only when no active account exists."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--email",
            default=os.getenv("LOCAL_BOOTSTRAP_EMAIL", "owner@crowdsmarter.local"),
        )
        parser.add_argument("--password", default=os.getenv("LOCAL_BOOTSTRAP_PASSWORD", ""))
        parser.add_argument("--first-name", default="Local")
        parser.add_argument("--last-name", default="Owner")
        parser.add_argument("--organisation", default="CrowdSmarter Local Workspace")

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        if not settings.DEBUG:
            raise CommandError("ensure_local_owner is available only when DJANGO_DEBUG=true.")

        active_count = User.objects.filter(is_active=True).count()
        if active_count:
            self.stdout.write(f"LOCAL_ACCESS_AVAILABLE active_accounts={active_count}")
            return

        email = options["email"].strip().lower()
        password = options["password"] or self._generated_password()
        organisation_name = options["organisation"].strip()
        if not email:
            raise CommandError("A local owner email is required.")

        user, created = User.objects.get_or_create(
            email__iexact=email,
            defaults={
                "email": email,
                "first_name": options["first_name"].strip(),
                "last_name": options["last_name"].strip(),
                "is_active": True,
            },
        )
        if not created:
            user.email = email
            user.is_active = True
            user.first_name = user.first_name or options["first_name"].strip()
            user.last_name = user.last_name or options["last_name"].strip()
        validate_password(password, user=user)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save()

        slug_base = slugify(organisation_name)[:70] or "crowdsmarter-local"
        organisation = Organisation.objects.filter(slug=slug_base).first()
        if organisation is None:
            slug = slug_base
            counter = 2
            while Organisation.objects.filter(slug=slug).exists():
                slug = f"{slug_base[:70-len(str(counter))-1]}-{counter}"
                counter += 1
            organisation = Organisation.objects.create(
                name=organisation_name,
                slug=slug,
                created_by=user,
            )
        Membership.objects.update_or_create(
            organisation=organisation,
            user=user,
            defaults={"role": Membership.Role.OWNER, "status": Membership.Status.ACTIVE},
        )
        Workspace.objects.get_or_create(
            organisation=organisation,
            slug="decisions",
            defaults={
                "name": "Decisions",
                "description": "The organisation's primary decision workspace.",
                "is_default": True,
                "created_by": user,
            },
        )

        self.stdout.write("LOCAL_ACCESS_CREATED")
        self.stdout.write(f"email={email}")
        self.stdout.write(f"password={password}")
        self.stdout.write("Change this password from Account settings after signing in.")

    @staticmethod
    def _generated_password() -> str:
        return f"Cs!{secrets.token_urlsafe(18)}9a"
