"""Invitation token generation and keyed hashing."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from django.conf import settings


def generate_token() -> str:
    """Return an unguessable URL-safe invitation secret."""
    return secrets.token_urlsafe(32)


def digest_token(raw_token: str) -> str:
    """Create the stable keyed digest stored in PostgreSQL."""
    return hmac.new(
        key=settings.SECRET_KEY.encode("utf-8"),
        msg=raw_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
