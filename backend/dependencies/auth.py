"""Authentication and RBAC Dependency Guards."""

from typing import Optional, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, VolunteerProfile
from backend.utils.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    bearer_auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[str]:
    """Extracts access token from Authorization header (Bearer) or from cookie."""
    if bearer_auth and bearer_auth.credentials:
        return bearer_auth.credentials
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT access token, checks live database account status,
    and dynamically enforces token_version.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        token_version = payload.get("token_version")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated or suspended."
        )

    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been invalidated due to security event or password change."
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str], require_approved_volunteer: bool = False):
        self.allowed_roles = allowed_roles
        self.require_approved_volunteer = require_approved_volunteer

    def __call__(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        # Enforce live database role check (never trust stale JWT claims)
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(self.allowed_roles)}."
            )

        # If volunteer access requires approval
        if self.require_approved_volunteer and current_user.role == "volunteer":
            profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == current_user.id).first()
            if not profile or profile.approval_status != "APPROVED":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Volunteer account is pending administrator approval."
                )

        return current_user


# Role Guards
require_authenticated_user = get_current_user
require_pilgrim = RoleChecker(["pilgrim", "volunteer", "coordinator", "admin"])
require_approved_volunteer = RoleChecker(["volunteer", "coordinator", "admin"], require_approved_volunteer=True)
require_coordinator = RoleChecker(["coordinator", "admin"])
require_admin = RoleChecker(["admin"])

