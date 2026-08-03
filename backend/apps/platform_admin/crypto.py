"""At-rest encryption for operator-supplied secrets (e.g. AI provider API keys).

Unlike passwords, invitation tokens, and MFA backup codes elsewhere in this
codebase, a provider API key must be recoverable in plaintext to actually
call the provider - so it cannot use the usual one-way keyed-digest pattern.
It is instead encrypted at rest with a key derived from ``SECRET_KEY``,
decrypted only at the moment of use, and never written to logs, audit
metadata, or API responses.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored secret could not be decrypted.") from exc
