"""Securely reset a local-development password from standard input."""

from __future__ import annotations

import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import set_new_password

User = get_user_model()


class Command(BaseCommand):
    """Reset one local account without putting the password in shell history."""

    help = "Reset a local account password; the new password is read from standard input."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument("--email", required=True)
        parser.add_argument("--activate", action="store_true")

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        if not settings.DEBUG:
            raise CommandError("reset_local_password is available only when DJANGO_DEBUG=true.")
        password = sys.stdin.readline().rstrip("\r\n")
        if not password:
            raise CommandError("No password was provided on standard input.")
        email = options["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError("No local account matches that email address.") from exc
        validate_password(password, user=user)
        if options["activate"] and not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        set_new_password(user=user, new_password=password, actor=None)
        self.stdout.write(self.style.SUCCESS(f"Password reset for {user.email}."))
