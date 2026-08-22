"""The always-available default: no automatic enrichment, the organiser verifies by hand."""

from __future__ import annotations

from .base import OrganisationLookupResult, ProviderConnectionResult


class ManualLookupProvider:
    key = "manual"
    label = "Manual verification"

    def lookup(self, *, query: str) -> OrganisationLookupResult:
        return OrganisationLookupResult(
            ok=True,
            found=False,
            detail="No lookup provider is configured — verify this organisation manually.",
        )

    def test_connection(self) -> ProviderConnectionResult:
        return ProviderConnectionResult(ok=True, detail="Manual verification requires no external connection.")
