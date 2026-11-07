"""Authentication and User Account API Routes for Warkari."""

import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, VolunteerProfile
from backend.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
    VolunteerApprovalRequest,
    UserRoleUpdateRequest
)
from backend.services.auth_service import auth_service
from backend.services.audit_service import audit_service
from backend.dependencies.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Accounts"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public user and volunteer registration"
)
async def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Public registration endpoint.
    - Permits 'pilgrim' or 'volunteer'.
    - Rejects 'coordinator' or 'admin'.
    """
    user = auth_service.register_user(db, payload)
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user.id).first()
    return UserProfileResponse(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        preferred_language=user.preferred_language,
        is_active=user.is_active,
        is_phone_verified=user.is_phone_verified,
        created_at=user.created_at,
        volunteer_status=profile.approval_status if profile else None,
        volunteer_sector=profile.sector if profile else None
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login with rate limiting & session creation"
)
async def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verifies credentials, creates a user session, issues JWT access token,
    and sets HttpOnly refresh token cookie.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, access_token, raw_refresh = auth_service.login_user(
        db=db,
        payload=payload,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Set secure HttpOnly cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=900,
        user_id=user.id,
        name=user.name,
        role=user.role,
        refresh_token=raw_refresh  # Provided for non-browser/CLI clients
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token with refresh token rotation (RTR)"
)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Rotates refresh token and issues fresh access token. Detects token reuse.
    """
    # Check payload first (so explicit request body overrides test client cookie jars)
    raw_token = payload.refresh_token if (payload and payload.refresh_token) else request.cookies.get("refresh_token")

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token must be provided via cookie or request body."
        )

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, new_access_token, new_raw_refresh = auth_service.refresh_session(
        db=db,
        raw_refresh_token=raw_token,
        ip_address=client_ip,
        user_agent=user_agent
    )

    response.set_cookie(
        key="refresh_token",
        value=new_raw_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth"
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=900,
        user_id=user.id,
        name=user.name,
        role=user.role,
        refresh_token=new_raw_refresh
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active user session and clear cookies"
)
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db)
):
    # Check payload first (so explicit request body overrides test client cookie jars)
    raw_token = payload.refresh_token if (payload and payload.refresh_token) else request.cookies.get("refresh_token")

    auth_service.logout_session(db, raw_token)

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out successfully."}


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user profile"
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == current_user.id).first()
    return UserProfileResponse(
        id=current_user.id,
        name=current_user.name,
        phone=current_user.phone,
        email=current_user.email,
        role=current_user.role,
        preferred_language=current_user.preferred_language,
        is_active=current_user.is_active,
        is_phone_verified=current_user.is_phone_verified,
        created_at=current_user.created_at,
        volunteer_status=profile.approval_status if profile else None,
        volunteer_sector=profile.sector if profile else None
    )


# ----------------------------------------------------------------------
# Administrative Actions: Volunteer Approval and Role Management
# ----------------------------------------------------------------------
@router.put(
    "/volunteers/{volunteer_id}/approve",
    summary="Administrator approval/rejection of volunteer profiles"
)
async def approve_volunteer(
    volunteer_id: int,
    payload: VolunteerApprovalRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == volunteer_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Volunteer profile not found.")

    status_val = payload.approval_status.upper()
    if status_val not in ["APPROVED", "REJECTED", "SUSPENDED"]:
        raise HTTPException(status_code=400, detail="Invalid approval status.")

    profile.approval_status = status_val
    if payload.sector:
        profile.sector = payload.sector
    profile.updated_at = datetime.datetime.utcnow()

    db.commit()

    audit_service.log_event(
        db=db,
        action="VOLUNTEER_APPROVAL_CHANGE",
        target_type="volunteer_profile",
        target_id=str(profile.id),
        actor_id=admin_user.id,
        details={"new_status": status_val}
    )

    return {"message": f"Volunteer status updated to {status_val}."}


@router.put(
    "/users/{user_id}/role",
    summary="Administrator role assignment"
)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_role = payload.role.strip().lower()
    if new_role not in ["pilgrim", "volunteer", "coordinator", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role.")

    old_role = target_user.role
    target_user.role = new_role
    target_user.token_version += 1  # Invalidate previous tokens so new role takes effect cleanly
    db.commit()

    audit_service.log_event(
        db=db,
        action="USER_ROLE_CHANGED",
        target_type="user",
        target_id=str(target_user.id),
        actor_id=admin_user.id,
        details={"old_role": old_role, "new_role": new_role}
    )

    return {"message": f"User role updated from {old_role} to {new_role}."}
