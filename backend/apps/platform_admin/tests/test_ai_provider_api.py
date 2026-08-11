import json

import pytest
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.platform_admin.models import PlatformAdministrator, PlatformConfiguration


def grant_platform_capability(user, rationale="Responsible for CrowdSmarter tenant operations."):
    return PlatformAdministrator.objects.create(
        user=user,
        rationale=rationale,
        status=PlatformAdministrator.Status.ACTIVE,
    )


@pytest.mark.django_db
def test_configuration_defaults_to_rules_with_no_key_set(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.get(reverse("platform_admin:platform-admin-configuration"))

    assert response.status_code == 200
    body = response.json()
    assert body["ai_provider_key"] == "rules"
    assert body["ai_provider_api_key_is_set"] is False


@pytest.mark.django_db
def test_non_administrator_cannot_read_or_change_ai_provider(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user)

    assert api_client.get(reverse("platform_admin:platform-admin-configuration")).status_code == 403
    assert api_client.patch(
        reverse("platform_admin:platform-admin-ai-provider"),
        {"provider_key": "rules", "model": "x", "rationale": "irrelevant, should be rejected first"},
        format="json",
    ).status_code == 403
    assert api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"api_key": "sk-ant-test", "rationale": "irrelevant, should be rejected first"},
        format="json",
    ).status_code == 403
    assert api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-test-connection"),
    ).status_code == 403


@pytest.mark.django_db
def test_test_connection_succeeds_locally_for_the_default_rules_provider(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.post(reverse("platform_admin:platform-admin-ai-provider-test-connection"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["provider_key"] == "rules"
    assert body["provider_label"] == "Transparent rules review"
    assert body["detail"]


@pytest.mark.django_db
def test_test_connection_reports_failure_when_a_keyed_provider_has_no_key(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)
    config = PlatformConfiguration.load()
    config.ai_provider_key = PlatformConfiguration.AIProviderKey.ANTHROPIC
    config.save(update_fields=["ai_provider_key"])

    response = api_client.post(reverse("platform_admin:platform-admin-ai-provider-test-connection"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert "API key" in body["detail"]


@pytest.mark.django_db
def test_switching_to_anthropic_without_a_key_is_rejected(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.patch(
        reverse("platform_admin:platform-admin-ai-provider"),
        {
            "provider_key": "anthropic",
            "model": "claude-sonnet-5",
            "rationale": "Try switching before a key is configured.",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_setting_api_key_never_leaks_the_raw_value_into_the_audit_log(
    api_client, user_factory
):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)
    secret = "sk-ant-do-not-leak-1234567890"

    response = api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"api_key": secret, "rationale": "Enable the real-model reviewer for a pilot team."},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["ai_provider_api_key_is_set"] is True
    assert secret not in json.dumps(response.json())

    event = AuditEvent.objects.get(action="platform_configuration.ai_provider_api_key_set")
    assert secret not in json.dumps(event.metadata)
    assert event.metadata["key_last_4"] == secret[-4:]

    config = PlatformConfiguration.load()
    assert secret not in config.ai_provider_api_key_encrypted


@pytest.mark.django_db
def test_switching_to_anthropic_succeeds_once_a_key_is_set(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"api_key": "sk-ant-real-key", "rationale": "Enable the real-model reviewer."},
        format="json",
    )
    response = api_client.patch(
        reverse("platform_admin:platform-admin-ai-provider"),
        {
            "provider_key": "anthropic",
            "model": "claude-sonnet-5",
            "rationale": "Key is now configured; switch to the real reviewer.",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["ai_provider_key"] == "anthropic"

    config = PlatformConfiguration.load()
    assert config.ai_provider_key == "anthropic"


@pytest.mark.django_db
def test_clearing_the_key_reverts_an_active_anthropic_provider_to_rules(
    api_client, user_factory
):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)
    api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"api_key": "sk-ant-real-key", "rationale": "Enable the real-model reviewer."},
        format="json",
    )
    api_client.patch(
        reverse("platform_admin:platform-admin-ai-provider"),
        {"provider_key": "anthropic", "model": "claude-sonnet-5", "rationale": "Switch to the real reviewer."},
        format="json",
    )

    response = api_client.delete(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"rationale": "Revoking the pilot key after the trial ended."},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["ai_provider_key"] == "rules"
    assert response.json()["ai_provider_api_key_is_set"] is False
    assert AuditEvent.objects.filter(
        action="platform_configuration.ai_provider_api_key_cleared"
    ).exists()


@pytest.mark.django_db
def test_ai_provider_serializers_reject_unknown_fields(api_client, user_factory):
    administrator = user_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse("platform_admin:platform-admin-ai-provider-api-key"),
        {"api_key": "sk-ant-test", "rationale": "Valid rationale text here.", "unexpected": "nope"},
        format="json",
    )

    assert response.status_code == 400
