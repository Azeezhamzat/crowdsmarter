"""Provider unit tests: manual (always available) and Stripe (mocked HTTP, no real network)."""

from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
import pytest

from apps.disbursements.providers.manual import ManualDisbursementProvider
from apps.disbursements.providers.registry import get_provider
from apps.disbursements.providers.stripe_provider import StripeDisbursementProvider


def test_manual_provider_always_succeeds():
    provider = ManualDisbursementProvider()
    key = str(uuid.uuid4())
    result = provider.issue_payout(amount=Decimal("250.00"), currency="GBP", idempotency_key=key)
    assert result.ok is True
    assert result.status == "paid"
    assert result.external_reference.startswith("manual-")
    assert provider.test_connection().ok is True

    hinted = provider.issue_payout(
        amount=Decimal("250.00"),
        currency="GBP",
        idempotency_key=key,
        reference_hint="Water project",
    )
    assert hinted.external_reference == "Water project"


def test_registry_returns_manual_by_default():
    provider = get_provider(provider_key="manual")
    assert provider.key == "manual"
    stripe_provider = get_provider(provider_key="stripe", api_key="sk_test_x", account_id="acct_1")
    assert stripe_provider.key == "stripe"


def test_stripe_provider_reports_not_configured_without_credentials():
    provider = StripeDisbursementProvider()
    result = provider.issue_payout(
        amount=Decimal("100.00"), currency="USD", idempotency_key=str(uuid.uuid4())
    )
    assert result.ok is False
    assert "not fully configured" in result.detail


def test_stripe_provider_issues_transfer_on_success(monkeypatch):
    def fake_post(url, **kwargs):
        assert url.endswith("/transfers")
        assert kwargs["data"]["amount"] == "10000"
        assert kwargs["data"]["destination"] == "acct_1"
        assert kwargs["data"]["currency"] == "gbp"
        assert kwargs["headers"]["Idempotency-Key"] == idempotency_key
        return httpx.Response(200, json={"id": "tr_123"}, request=httpx.Request("POST", url))

    monkeypatch.setattr("apps.disbursements.providers.stripe_provider.httpx.post", fake_post)
    provider = StripeDisbursementProvider(api_key="sk_test_x", account_id="acct_1")
    idempotency_key = str(uuid.uuid4())
    result = provider.issue_payout(
        amount=Decimal("100.00"), currency="GBP", idempotency_key=idempotency_key
    )
    assert result.ok is True
    assert result.status == "paid"
    assert result.external_reference == "tr_123"


def test_stripe_provider_surfaces_rejection(monkeypatch):
    def fake_post(url, **kwargs):
        return httpx.Response(
            402,
            json={"error": {"message": "Your account cannot make transfers."}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("apps.disbursements.providers.stripe_provider.httpx.post", fake_post)
    provider = StripeDisbursementProvider(api_key="sk_test_x", account_id="acct_1")
    result = provider.issue_payout(
        amount=Decimal("100.00"), currency="USD", idempotency_key=str(uuid.uuid4())
    )
    assert result.ok is False
    assert "cannot make transfers" in result.detail


def test_stripe_provider_test_connection(monkeypatch):
    def fake_get(url, **kwargs):
        assert url.endswith("/balance")
        return httpx.Response(200, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr("apps.disbursements.providers.stripe_provider.httpx.get", fake_get)
    provider = StripeDisbursementProvider(api_key="sk_test_x", account_id="acct_1")
    result = provider.test_connection()
    assert result.ok is True


@pytest.mark.parametrize("api_key", ["", None])
def test_stripe_provider_test_connection_without_key(api_key):
    provider = StripeDisbursementProvider(api_key=api_key or "", account_id="acct_1")
    result = provider.test_connection()
    assert result.ok is False
