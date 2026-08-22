"""Configuration-driven provider loading, mirroring apps.ai_assistance.providers.registry."""

from __future__ import annotations

from .base import DisbursementProvider
from .manual import ManualDisbursementProvider
from .stripe_provider import StripeDisbursementProvider

PROVIDER_LABELS = {
    ManualDisbursementProvider.key: ManualDisbursementProvider.label,
    StripeDisbursementProvider.key: StripeDisbursementProvider.label,
}


def get_provider(*, provider_key: str, api_key: str = "", account_id: str = "") -> DisbursementProvider:
    if provider_key == StripeDisbursementProvider.key:
        return StripeDisbursementProvider(api_key=api_key, account_id=account_id)
    return ManualDisbursementProvider()
