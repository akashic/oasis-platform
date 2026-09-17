"""
OASIS — Password hashing for the single admin credential.

FINDING-005: ``AUTH_PASSWORD`` was stored and compared as plaintext. This
module adds an Argon2id path (``AUTH_PASSWORD_HASH``) and is used by
``app/api/auth.py``, which still accepts plaintext ``AUTH_PASSWORD`` as a
deprecated migration path (logs a warning) until operators migrate.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage in ``AUTH_PASSWORD_HASH``."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify ``password`` against a stored Argon2id hash.

    Returns ``False`` (never raises) on mismatch or a malformed/foreign hash.
    """
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHash, ValueError):
        return False
