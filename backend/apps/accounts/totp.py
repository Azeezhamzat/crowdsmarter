"""RFC 6238 TOTP (and its RFC 4226 HOTP basis), implemented with the standard
library only - no external service or dependency is needed for MFA.

The HOTP truncation step is verified in tests against the official RFC 4226
Appendix D test vectors.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

DIGITS = 6
PERIOD_SECONDS = 30


def generate_secret() -> str:
    """Return a random base32-encoded shared secret (160 bits of entropy)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def _hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret.upper())
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(truncated % (10**DIGITS)).zfill(DIGITS)


def verify_totp(*, secret: str, code: str, window: int = 1, at: float | None = None) -> bool:
    """Accept a code from the current 30s step or +/- `window` steps for clock drift."""
    code = code.strip().replace(" ", "")
    if not code.isdigit() or len(code) != DIGITS:
        return False
    counter = int((at if at is not None else time.time()) // PERIOD_SECONDS)
    return any(
        hmac.compare_digest(_hotp(secret, counter + offset), code)
        for offset in range(-window, window + 1)
    )


def provisioning_uri(*, secret: str, email: str, issuer: str = "CrowdSmarter") -> str:
    """Return an otpauth:// URI suitable for a QR code or manual entry link."""
    label = quote(f"{issuer}:{email}")
    query = f"secret={secret}&issuer={quote(issuer)}&digits={DIGITS}&period={PERIOD_SECONDS}"
    return f"otpauth://totp/{label}?{query}"
