"""Rate Limiting Utility for Sensitive Public Endpoints."""

import time
from collections import defaultdict
from fastapi import HTTPException, Request, status

# In-memory token bucket rate limiter: IP -> list of timestamps
_tracking_rate_limits = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 10
WINDOW_SECONDS = 60


def rate_limit_public_tracking(request: Request) -> None:
    """Enforces 10 requests per minute per IP address."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _tracking_rate_limits[client_ip]

    # Purge timestamps older than window
    _tracking_rate_limits[client_ip] = [ts for ts in timestamps if now - ts < WINDOW_SECONDS]

    if len(_tracking_rate_limits[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many tracking requests. Rate limit is 10 requests per minute. Please try again later."
        )

    _tracking_rate_limits[client_ip].append(now)

