"""Security utility module for Warkari Authentication.

Implements:
- NIST-recommended Scrypt password hashing via python stdlib (hashlib.scrypt).
- Cryptographic access token (JWT) creation and decoding.
- Refresh token generation and HMAC-SHA256 hashing.
"""

import os
import hmac
import base64
import secrets
import hashlib
import datetime
from typing import Dict, Any, Optional, Tuple
import jwt
from backend.config import get_settings

# Scrypt parameters (NIST / OWASP recommended: N=16384, r=8, p=1, key_len=64)
SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hashes a password using Scrypt with a random 16-byte salt."""
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=0,
        dklen=SCRYPT_DKLEN
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(derived).decode("utf-8")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored Scrypt hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = base64.b64decode(parts[4])
        expected_hash = base64.b64decode(parts[5])

        derived = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=0,
            dklen=len(expected_hash)
        )
        return hmac.compare_digest(derived, expected_hash)
    except Exception:
        return False


def create_access_token(user_id: int, role: str, token_version: int, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Creates a signed short-lived JWT access token."""
    settings = get_settings()
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_version": token_version,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token."""
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def generate_refresh_token(secret_key: Optional[str] = None) -> Tuple[str, str]:
    """
    Generates a 256-bit URL-safe random refresh token and its HMAC-SHA256 hash.
    Returns: (raw_refresh_token, refresh_token_hash)
    """
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")
    raw_token = secrets.token_urlsafe(32)
    token_hash = hmac.new(key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str, secret_key: Optional[str] = None) -> str:
    """Computes HMAC-SHA256 hash of a provided raw refresh token."""
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")
    return hmac.new(key, raw_token.strip().encode("utf-8"), hashlib.sha256).hexdigest()

