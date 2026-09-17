"""
OASIS — Envelope encryption for credentials stored in Redis.

FINDING-006: ``PUT /api/settings/keys`` and ``PUT /api/settings/audio-storage``
persist provider credentials (~28 fields, incl. OpenAI/Anthropic/Twilio keys
and S3 access keys) to Redis in plaintext, and Redis itself has no auth/TLS.
Encrypting the values before ``HSET`` means a Redis read (via a compromised
container, the Docker socket, or a volume/backup) does not yield a usable
secret on its own — a second factor, ``SECRET_KEY``, is also required.

The key is derived from ``SECRET_KEY`` via HKDF with a fixed, purpose-specific
``info`` label so it is cryptographically independent of the JWT signing use
of the same setting (``app/auth.py``, ``app/api/twilio.py``).
"""

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import settings

_HKDF_INFO = b"oasis-redis-settings-encryption-v1"


def _fernet() -> Fernet:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_HKDF_INFO)
    key = base64.urlsafe_b64encode(hkdf.derive(settings.secret_key.encode("utf-8")))
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    """Encrypt ``value`` for storage in Redis. Empty strings pass through
    unchanged (an empty override means "cleared", handled by callers via
    ``HDEL`` before this is ever invoked)."""
    if not value:
        return value
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    """Decrypt a value previously stored via :func:`encrypt_secret`.

    Falls back to returning the raw value unchanged when it is not a valid
    Fernet token. This keeps values written before this fix (plaintext, from
    the previously-unencrypted store) readable until they are next rewritten
    via the dashboard, instead of breaking every existing deployment on
    upgrade.
    """
    if not value:
        return value
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeDecodeError, UnicodeEncodeError):
        return value
