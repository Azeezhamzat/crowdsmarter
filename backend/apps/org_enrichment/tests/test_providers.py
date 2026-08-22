from __future__ import annotations

import httpx
import pytest

from apps.org_enrichment.providers.candid import CandidLookupProvider
from apps.org_enrichment.providers.manual import ManualLookupProvider
from apps.org_enrichment.providers.registry import get_provider


def test_manual_provider_reports_no_automatic_lookup():
    provider = ManualLookupProvider()
    result = provider.lookup(query="Water for All")
    assert result.ok is True
    assert result.found is False
    assert provider.test_connection().ok is True


def test_registry_returns_manual_by_default():
    assert get_provider(provider_key="manual").key == "manual"
    assert get_provider(provider_key="candid", api_key="key123").key == "candid"


def test_candid_provider_reports_not_configured_without_key():
    provider = CandidLookupProvider()
    result = provider.lookup(query="12-3456789")
    assert result.ok is False


def test_candid_provider_returns_match(monkeypatch):
    def fake_get(url, **kwargs):
        assert kwargs["headers"]["Subscription-Key"] == "key123"
        return httpx.Response(
            200,
            json={"organization": {"organization_name": "Water for All", "ein": "12-3456789", "summary": "Clean water NGO", "subsection_code_description": "501(c)(3)"}},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("apps.org_enrichment.providers.candid.httpx.get", fake_get)
    provider = CandidLookupProvider(api_key="key123")
    result = provider.lookup(query="12-3456789")
    assert result.ok is True
    assert result.found is True
    assert result.legal_name == "Water for All"


def test_candid_provider_reports_not_found(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(404, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr("apps.org_enrichment.providers.candid.httpx.get", fake_get)
    provider = CandidLookupProvider(api_key="key123")
    result = provider.lookup(query="00-0000000")
    assert result.ok is True
    assert result.found is False


@pytest.mark.parametrize("status", [401, 403])
def test_candid_provider_test_connection_rejects_bad_key(monkeypatch, status):
    def fake_get(url, **kwargs):
        return httpx.Response(status, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr("apps.org_enrichment.providers.candid.httpx.get", fake_get)
    provider = CandidLookupProvider(api_key="bad-key")
    assert provider.test_connection().ok is False
