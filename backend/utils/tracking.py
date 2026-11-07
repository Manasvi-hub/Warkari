"""Utility functions for Incident Tracking Tokens and Public References."""

import hmac
import hashlib
import secrets
import string
from typing import Tuple
from backend.config import get_settings


def generate_tracking_credentials(secret_key: str = None) -> Tuple[str, str, str]:
    """
    Generates:
    - raw_token: 256-bit URL-safe token returned once to pilgrim
    - token_hash: HMAC-SHA256 hex digest stored in database
    - public_ref: Non-sequential public reference (e.g. 'WKR-7X9K-4M2P')
    """
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")

    # 1. Generate 256-bit URL-safe random tracking token
    raw_token = secrets.token_urlsafe(32)

    # 2. Compute HMAC-SHA256 hash
    token_hash = hmac.new(key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()

    # 3. Generate non-sequential public reference: WKR-XXXX-XXXX
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters if desired, or use standard uppercase alphanumeric
    part1 = "".join(secrets.choice(alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(alphabet) for _ in range(4))
    public_ref = f"WKR-{part1}-{part2}"

    return raw_token, token_hash, public_ref


def hash_tracking_token(raw_token: str, secret_key: str = None) -> str:
    """Computes HMAC-SHA256 hash of a provided raw token."""
    settings = get_settings()
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")
    return hmac.new(key, raw_token.strip().encode("utf-8"), hashlib.sha256).hexdigest()

