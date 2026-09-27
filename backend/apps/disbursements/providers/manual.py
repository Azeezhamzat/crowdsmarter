"""The always-available default: an organiser records a payment made outside the platform."""

from __future__ import annotations

import uuid

from .base import DisbursementResult, ProviderConnectionResult


class ManualDisbursementProvider:
    key = "manual"
    label = "Manual ledger"

    def issue_payout(
        self,
        *,
        amount,
        currency: str,
        idempotency_key: str,
        reference_hint: str = "",
    ) -> DisbursementResult:
        del amount, currency
        reference = reference_hint.strip() or f"manual-{uuid.UUID(idempotency_key).hex[:12]}"
        return DisbursementResult(
            ok=True,
            status="paid",
            external_reference=reference,
            detail="Recorded as paid outside the platform.",
        )

    def test_connection(self) -> ProviderConnectionResult:
        return ProviderConnectionResult(
            ok=True, detail="The manual ledger requires no external connection."
        )
