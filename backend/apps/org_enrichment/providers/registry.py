"""Configuration-driven provider loading, mirroring apps.disbursements.providers.registry."""

from __future__ import annotations

from .base import OrganisationLookupProvider
from .candid import CandidLookupProvider
from .manual import ManualLookupProvider


def get_provider(*, provider_key: str, api_key: str = "") -> OrganisationLookupProvider:
    if provider_key == CandidLookupProvider.key:
        return CandidLookupProvider(api_key=api_key)
    return ManualLookupProvider()
