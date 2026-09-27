"""Candid (Essentials API) organisation lookup - code-complete, reachable once an org sets its own key.

Like the Stripe disbursement provider, this uses httpx directly rather than
adding a dedicated SDK dependency. Candid's Essentials API is keyed by EIN
and authenticated with a `Subscription-Key` header; the exact response shape
should be re-checked against Candid's current API reference before a real
production key is ever entered, but the request/response/error handling
shape here is stable and fully unit-testable against mocked HTTP.
"""

from __future__ import annotations

import httpx

from .base import OrganisationLookupResult, ProviderConnectionResult

CANDID_API_BASE = "https://api.candid.org/essentials/v3"


class CandidLookupProvider:
    key = "candid"
    label = "Candid (GuideStar)"

    def __init__(self, *, api_key: str = "") -> None:
        self.api_key = api_key

    def lookup(self, *, query: str) -> OrganisationLookupResult:
        if not self.api_key:
            return OrganisationLookupResult(
                ok=False, found=False, detail="No Candid API key is configured."
            )
        try:
            response = httpx.get(
                f"{CANDID_API_BASE}/{query.strip()}",
                headers={"Subscription-Key": self.api_key},
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            return OrganisationLookupResult(
                ok=False, found=False, detail=f"Candid request failed: {exc}"
            )
        if response.status_code == 404:
            return OrganisationLookupResult(
                ok=True, found=False, detail="No matching organisation was found."
            )
        if response.status_code >= 400:
            return OrganisationLookupResult(
                ok=False, found=False, detail="Candid rejected the request."
            )
        payload = response.json()
        organisation = payload.get("organization", payload)
        return OrganisationLookupResult(
            ok=True,
            found=True,
            legal_name=organisation.get("organization_name", ""),
            ein_or_charity_number=organisation.get("ein", query),
            financial_summary=organisation.get("summary", ""),
            standing=organisation.get("subsection_code_description", ""),
            detail="Retrieved from Candid.",
        )

    def test_connection(self) -> ProviderConnectionResult:
        if not self.api_key:
            return ProviderConnectionResult(ok=False, detail="No Candid API key is configured.")
        try:
            response = httpx.get(
                f"{CANDID_API_BASE}/00-0000000",
                headers={"Subscription-Key": self.api_key},
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            return ProviderConnectionResult(ok=False, detail=f"Candid request failed: {exc}")
        if response.status_code in (401, 403):
            return ProviderConnectionResult(
                ok=False, detail="Candid rejected the configured API key."
            )
        return ProviderConnectionResult(ok=True, detail="Connected to Candid.")
