"""Grant CrowdSmarter's explicit platform-administrator capability."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.organisations.models import Membership, Organisation
from apps.platform_admin.models import PlatformAdministrator, PlatformConfiguration

SIMULATED_SLUGS = (
    "northstar-grid-services-sim",
    "careweave-regional-health-sim",
    "terrafood-futures-institute-sim",
)


class Command(BaseCommand):
    help = (
        "Grant an existing active account CrowdSmarter's explicit platform-administrator "
        "capability. Simulated organisations may optionally receive owner membership."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--email",
            default=getattr(settings, "PLATFORM_ADMIN_EMAIL", ""),
            help="Existing account email. Defaults to PLATFORM_ADMIN_EMAIL.",
        )
        parser.add_argument(
            "--demo-organisations",
            action="store_true",
            help="Grant active owner membership only in the three fictional demo organisations.",
        )
        parser.add_argument(
            "--technical-admin",
            action="store_true",
            help="Also set Django is_staff/is_superuser for emergency technical administration.",
        )
        parser.add_argument(
            "--rationale",
            default="Named CrowdSmarter platform operator responsible for tenant governance.",
        )
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        email = str(options["email"] or "").strip().lower()
        rationale = str(options["rationale"] or "").strip()
        if not email:
            raise CommandError("Provide --email or configure PLATFORM_ADMIN_EMAIL.")
        if len(rationale) < 12:
            raise CommandError("Provide a meaningful --rationale of at least 12 characters.")

        User = get_user_model()
        try:
            user = User.objects.select_for_update().get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError(f"No CrowdSmarter account exists for {email}.") from exc
        if not user.is_active:
            raise CommandError("Reactivate the account before granting platform administration.")

        PlatformConfiguration.objects.get_or_create(singleton_key=1)
        capability, created = PlatformAdministrator.objects.select_for_update().get_or_create(
            user=user,
            defaults={"status": "active", "rationale": rationale},
        )
        if not created:
            capability.status = "active"
            capability.rationale = rationale
            capability.suspended_by = None
            capability.suspended_at = None
            capability.save(
                update_fields=["status", "rationale", "suspended_by", "suspended_at", "updated_at"]
            )

        changed_flags: list[str] = []
        if options["technical_admin"]:
            for field in ("is_staff", "is_superuser"):
                if not getattr(user, field):
                    setattr(user, field, True)
                    changed_flags.append(field)
            if changed_flags:
                user.save(update_fields=changed_flags)

        demo_memberships = 0
        if options["demo_organisations"]:
            for organisation in Organisation.objects.filter(slug__in=SIMULATED_SLUGS):
                Membership.objects.update_or_create(
                    organisation=organisation,
                    user=user,
                    defaults={"role": Membership.Role.OWNER, "status": Membership.Status.ACTIVE},
                )
                demo_memberships += 1

        mode = "DRY RUN" if options["dry_run"] else "APPLIED"
        self.stdout.write(self.style.SUCCESS(f"{mode}: platform administrator {user.email}"))
        self.stdout.write(f"Capability status: {capability.status}")
        self.stdout.write(f"Technical admin flags changed: {', '.join(changed_flags) or 'none'}")
        self.stdout.write(f"Demo organisation owner memberships: {demo_memberships}")
        if options["dry_run"]:
            transaction.set_rollback(True)
