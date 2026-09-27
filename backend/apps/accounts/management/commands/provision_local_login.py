"""Provision deterministic local access for an explicitly requested email."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.organisations.models import Membership, MembershipEvent, Organisation
from apps.organisations.services import create_organisation

User = get_user_model()


class Command(BaseCommand):
    """Create or repair one local login and write the temporary password securely."""

    help = "Provision a requested local-development login and write credentials to a mode-600 file."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument("--email", required=True)
        parser.add_argument("--credentials-file", required=True)
        parser.add_argument("--first-name", default="Azeez")
        parser.add_argument("--last-name", default="Hamzat")
        parser.add_argument("--organisation", default="Azeez CrowdSmarter Workspace")
        parser.add_argument("--ensure-owner", action="store_true")

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        if not settings.DEBUG:
            raise CommandError("provision_local_login is available only when DJANGO_DEBUG=true.")
        email = options["email"].strip().lower()
        if not email:
            raise CommandError("An email address is required.")
        credentials_path = Path(options["credentials_file"]).expanduser().resolve()
        password = f"Cs!{secrets.token_urlsafe(20)}9a"

        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if user is None:
            user = User(email=email)
        user.email = email
        user.is_active = True
        user.first_name = user.first_name or options["first_name"].strip()
        user.last_name = user.last_name or options["last_name"].strip()
        validate_password(password, user=user)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save()

        active_membership = (
            Membership.objects.filter(user=user, status=Membership.Status.ACTIVE)
            .select_related("organisation")
            .first()
        )
        if active_membership is None:
            organisation_name = options["organisation"].strip()
            slug_base = slugify(organisation_name)[:70] or "crowdsmarter-local"
            slug = slug_base
            counter = 2
            while Organisation.objects.filter(slug=slug).exists():
                slug = f"{slug_base[: 70 - len(str(counter)) - 1]}-{counter}"
                counter += 1
            organisation = create_organisation(actor=user, name=organisation_name, slug=slug)
            active_membership = Membership.objects.get(organisation=organisation, user=user)
        else:
            organisation = active_membership.organisation

        if options["ensure_owner"] and active_membership.role != Membership.Role.OWNER:
            previous_role = active_membership.role
            active_membership.role = Membership.Role.OWNER
            active_membership.save(update_fields=["role", "updated_at"])
            MembershipEvent.objects.create(
                organisation=organisation,
                membership_id_snapshot=active_membership.id,
                user=user,
                actor=user,
                kind=MembershipEvent.Kind.ROLE_CHANGED,
                previous_role=previous_role,
                new_role=Membership.Role.OWNER,
                previous_status=active_membership.status,
                new_status=active_membership.status,
                note="Local-debug owner access provisioned explicitly.",
            )

        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        old_umask = os.umask(0o077)
        try:
            credentials_path.write_text(
                "CrowdSmarter local login\n"
                "========================\n\n"
                f"Email: {email}\n"
                f"Temporary password: {password}\n"
                f"Organisation: {organisation.name}\n"
                "Sign in: http://localhost:5173/login\n\n"
                "Change the password from Account settings after signing in, then delete this file.\n",
                encoding="utf-8",
            )
            credentials_path.chmod(0o600)
        finally:
            os.umask(old_umask)

        self.stdout.write("LOCAL_LOGIN_PROVISIONED")
        self.stdout.write(f"email={email}")
        self.stdout.write(f"created={'yes' if created else 'no'}")
        self.stdout.write(f"credentials_file={credentials_path}")
