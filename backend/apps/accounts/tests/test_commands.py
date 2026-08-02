"""Local-development access recovery commands."""

from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings

from apps.organisations.models import Membership, Organisation

User = get_user_model()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_ensure_local_owner_bootstraps_only_an_empty_installation():
    output = StringIO()
    call_command(
        "ensure_local_owner",
        email="owner@example.local",
        password="A-secure-local-password-123",
        stdout=output,
    )

    user = User.objects.get(email="owner@example.local")
    assert user.check_password("A-secure-local-password-123")
    organisation = Organisation.objects.get()
    membership = Membership.objects.get(organisation=organisation, user=user)
    assert membership.role == Membership.Role.OWNER
    assert "LOCAL_ACCESS_CREATED" in output.getvalue()

    second_output = StringIO()
    call_command("ensure_local_owner", stdout=second_output)
    assert User.objects.count() == 1
    assert "LOCAL_ACCESS_AVAILABLE" in second_output.getvalue()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_reset_local_password_reads_secret_from_stdin(
    user_factory, monkeypatch
):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="Old-password-123")
    monkeypatch.setattr("sys.stdin", StringIO("New-secure-password-456\n"))
    call_command("reset_local_password", email="PERSON@example.com")
    user.refresh_from_db()
    assert user.check_password("New-secure-password-456")


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_local_access_commands_refuse_production(
    user_factory, monkeypatch
):  # type: ignore[no-untyped-def]
    from django.core.management import CommandError

    user_factory(email="person@example.com", password="Old-password-123")
    with pytest.raises(CommandError, match="only when DJANGO_DEBUG"):
        call_command("ensure_local_owner")

    monkeypatch.setattr("sys.stdin", StringIO("New-secure-password-456\n"))
    with pytest.raises(CommandError, match="only when DJANGO_DEBUG"):
        call_command("reset_local_password", email="person@example.com")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_provision_local_login_guarantees_requested_email_and_secure_file(tmp_path):
    credentials = tmp_path / "local-access.txt"
    output = StringIO()
    call_command(
        "provision_local_login",
        email="owner@example.test ",
        credentials_file=str(credentials),
        ensure_owner=True,
        stdout=output,
    )
    user = User.objects.get(email="owner@example.test")
    content = credentials.read_text(encoding="utf-8")
    password_line = next(line for line in content.splitlines() if line.startswith("Temporary password:"))
    password = password_line.split(":", 1)[1].strip()
    assert user.is_active
    assert user.check_password(password)
    membership = Membership.objects.get(user=user, status=Membership.Status.ACTIVE)
    assert membership.role == Membership.Role.OWNER
    assert credentials.stat().st_mode & 0o777 == 0o600
    assert "LOCAL_LOGIN_PROVISIONED" in output.getvalue()


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_provision_local_login_refuses_production(tmp_path):
    from django.core.management import CommandError

    with pytest.raises(CommandError, match="only when DJANGO_DEBUG"):
        call_command(
            "provision_local_login",
            email="owner@example.test",
            credentials_file=str(tmp_path / "credentials.txt"),
        )
