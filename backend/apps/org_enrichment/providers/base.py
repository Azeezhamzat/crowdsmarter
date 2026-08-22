"""Provider-neutral contract for looking up an applicant organisation's public profile."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class OrganisationLookupResult:
    ok: bool
    found: bool
    legal_name: str = ""
    ein_or_charity_number: str = ""
    financial_summary: str = ""
    standing: str = ""
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderConnectionResult:
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class OrganisationLookupProvider(Protocol):
    """Replaceable provider contract. A configuration always has one active provider."""

    key: str
    label: str

    def lookup(self, *, query: str) -> OrganisationLookupResult:
        """Look up an organisation by name or registration number. Never raises for a provider-side failure."""

    def test_connection(self) -> ProviderConnectionResult:
        """Make the smallest possible check to confirm the provider is reachable/configured."""
