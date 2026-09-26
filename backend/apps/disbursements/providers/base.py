"""Provider-neutral contract for issuing a funded grant's payout."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DisbursementResult:
    ok: bool
    status: str
    external_reference: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderConnectionResult:
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DisbursementProvider(Protocol):
    """Replaceable provider contract. A configuration always has one active provider."""

    key: str
    label: str

    def issue_payout(
        self,
        *,
        amount,
        currency: str,
        idempotency_key: str,
        reference_hint: str = "",
    ) -> DisbursementResult:
        """Move (or record) a payment for a funded application. Never raises for a provider-side failure."""

    def test_connection(self) -> ProviderConnectionResult:
        """Make the smallest possible check to confirm the provider is reachable/configured."""
