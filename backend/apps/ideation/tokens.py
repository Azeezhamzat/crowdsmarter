"""Session identifiers: a shareable slug and a per-participant bearer token."""

from __future__ import annotations

import secrets

from apps.invitations.tokens import digest_token, generate_token

__all__ = ["digest_token", "generate_token", "generate_public_slug"]


def generate_public_slug() -> str:
    """Return a short, URL-safe identifier meant to be shared widely (not a secret)."""
    return secrets.token_urlsafe(9)
