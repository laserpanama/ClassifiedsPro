"""
Encrypts credentials at rest using Fernet (symmetric, authenticated encryption).

The key comes from the CREDENTIAL_ENCRYPTION_KEY environment variable.
If it is not set, an ephemeral in-memory key is generated at startup and a
warning is logged — encrypted values written this way are unreadable after a
restart, so production deployments MUST set the variable.

For backwards compatibility with rows written before encryption was introduced,
`decrypt_text` falls back to returning the input unchanged when it cannot be
decrypted (which is exactly what legacy plaintext looks like). Re-saving an
account re-encrypts its password, so storage converges to fully-encrypted over
time.
"""
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ephemeral_key: bytes | None = None


def _get_fernet() -> Fernet:
    key = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "").strip()
    if key:
        return Fernet(key.encode("utf-8"))

    global _ephemeral_key
    if _ephemeral_key is None:
        logger.warning(
            "CREDENTIAL_ENCRYPTION_KEY is not set. Generated an ephemeral key — "
            "encrypted credentials will NOT survive a restart. Set it in app/backend/.env."
        )
        _ephemeral_key = Fernet.generate_key()
    return Fernet(_ephemeral_key)


def encrypt_text(plaintext: str) -> str:
    if plaintext is None:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str) -> str:
    if value is None:
        return value
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        # Legacy plaintext (or a key change): return as-is and let the caller log.
        logger.warning(
            "Could not decrypt a stored credential with the configured key. "
            "Treating it as legacy plaintext — re-save the account to re-encrypt it."
        )
        return value


def generate_key() -> str:
    """Helper for operators: python -c "from app.backend.services.crypto_service import generate_key; print(generate_key())"""
    return Fernet.generate_key().decode("utf-8")
