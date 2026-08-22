"""Stripe Connect transfers - code-complete, but only reachable once an org's own keys are set.

Uses httpx directly against Stripe's plain REST API rather than the ``stripe``
SDK, since httpx already ships transitively via the anthropic/openai clients
and Stripe's transfer/balance endpoints need nothing the SDK adds. Every
failure mode (missing config, network error, Stripe-side rejection) returns a
normal result object rather than raising, so a mis-set key never crashes the
disbursement flow - it just reports as not-ok.
"""

from __future__ import annotations

from decimal import Decimal

import httpx

from .base import DisbursementResult, ProviderConnectionResult

STRIPE_API_BASE = "https://api.stripe.com/v1"


class StripeDisbursementProvider:
    key = "stripe"
    label = "Stripe Connect"

    def __init__(self, *, api_key: str = "", account_id: str = "") -> None:
        self.api_key = api_key
        self.account_id = account_id

    def issue_payout(self, *, amount: Decimal, reference_hint: str = "") -> DisbursementResult:
        if not self.api_key or not self.account_id:
            return DisbursementResult(
                ok=False, status="failed", external_reference="",
                detail="Stripe is not fully configured - set an API key and connected account first.",
            )
        try:
            response = httpx.post(
                f"{STRIPE_API_BASE}/transfers",
                auth=(self.api_key, ""),
                data={
                    "amount": str(int(Decimal(amount) * 100)),
                    "currency": "usd",
                    "destination": self.account_id,
                    "description": reference_hint or "CrowdSmarter grant disbursement",
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            return DisbursementResult(ok=False, status="failed", external_reference="", detail=f"Stripe request failed: {exc}")
        if response.status_code >= 400:
            detail = "Stripe rejected the transfer."
            try:
                detail = response.json().get("error", {}).get("message", detail)
            except ValueError:
                pass
            return DisbursementResult(ok=False, status="failed", external_reference="", detail=detail)
        payload = response.json()
        return DisbursementResult(ok=True, status="paid", external_reference=payload.get("id", ""), detail="Stripe transfer created.")

    def test_connection(self) -> ProviderConnectionResult:
        if not self.api_key:
            return ProviderConnectionResult(ok=False, detail="No Stripe API key is configured.")
        try:
            response = httpx.get(f"{STRIPE_API_BASE}/balance", auth=(self.api_key, ""), timeout=10.0)
        except httpx.HTTPError as exc:
            return ProviderConnectionResult(ok=False, detail=f"Stripe request failed: {exc}")
        if response.status_code >= 400:
            return ProviderConnectionResult(ok=False, detail="Stripe rejected the configured API key.")
        return ProviderConnectionResult(ok=True, detail="Connected to Stripe.")
