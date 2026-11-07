"""Authentication and Account Service for Warkari Platform."""

import uuid
import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models import User, UserSession, VolunteerProfile, Volunteer
from backend.schemas import UserRegisterRequest, UserLoginRequest
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from backend.services.audit_service import audit_service

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    def register_user(self, db: Session, payload: UserRegisterRequest) -> User:
        """
        Registers a new user.
        Strict public registration rules:
        - Only 'pilgrim' or 'volunteer' can be self-requested.
        - Coordinator and Admin self-registration is strictly rejected.
        - Volunteers receive a VolunteerProfile in PENDING approval status.
        """
        requested_role = (payload.requested_role or "pilgrim").strip().lower()
        if requested_role in ["coordinator", "admin", "administrator"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Privileged roles (coordinator, admin) cannot be self-requested via public registration."
            )
        if requested_role not in ["pilgrim", "volunteer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid requested role. Must be 'pilgrim' or 'volunteer'."
            )

        clean_phone = payload.phone.strip()
        # Verify phone uniqueness
        existing_phone = db.query(User).filter(User.phone == clean_phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists."
            )

        # Verify email uniqueness if provided
        clean_email = payload.email.strip().lower() if payload.email else None
        if clean_email:
            existing_email = db.query(User).filter(User.email == clean_email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email address already exists."
                )

        hashed = hash_password(payload.password)

        new_user = User(
            name=payload.name.strip(),
            phone=clean_phone,
            email=clean_email,
            hashed_password=hashed,
            role=requested_role,
            preferred_language=payload.preferred_language or "mr",
            token_version=1,
            is_active=True,
            is_phone_verified=False,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # If volunteer, create linked VolunteerProfile in PENDING approval status
        if requested_role == "volunteer":
            # Also create legacy companion record to maintain 100% backward compatibility
            legacy_vol = Volunteer(
                name=new_user.name,
                phone=new_user.phone,
                assigned_area=payload.sector,
                availability="offline"
            )
            db.add(legacy_vol)
            db.commit()
            db.refresh(legacy_vol)

            profile = VolunteerProfile(
                user_id=new_user.id,
                legacy_volunteer_id=legacy_vol.id,
                skills=payload.skills,
                sector=payload.sector,
                availability="offline",
                approval_status="PENDING",
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            db.add(profile)
            db.commit()

        audit_service.log_event(
            db=db,
            action="USER_REGISTERED",
            target_type="user",
            target_id=str(new_user.id),
            actor_id=new_user.id,
            details={"role": requested_role}
        )

        return new_user

    def login_user(
        self,
        db: Session,
        payload: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticates user, enforces failed attempts lockout,
        creates user_session, and returns (user, access_token, raw_refresh_token).
        """
        clean_phone = payload.phone.strip()
        user = db.query(User).filter(User.phone == clean_phone).first()

        now = datetime.datetime.utcnow()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password."
            )

        # Check account lockout
        if user.locked_until and user.locked_until > now:
            remaining_mins = int((user.locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is temporarily locked due to repeated failed logins. Please try again in {remaining_mins} minutes."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended or deactivated."
            )

        # Verify password
        if not verify_password(payload.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + datetime.timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_login_attempts = 0
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account locked for {LOCKOUT_MINUTES} minutes due to multiple failed login attempts."
                )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or password."
            )

        # Successful login: reset failed attempts counter
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        # Issue tokens
        access_token = create_access_token(user.id, user.role, user.token_version)
        raw_refresh, refresh_hash = generate_refresh_token()

        session_id = str(uuid.uuid4())
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            created_at=now,
            expires_at=now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            last_used_at=now,
            is_revoked=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(user_session)
        db.commit()

        audit_service.log_event(
            db=db,
            action="USER_LOGIN_SUCCESS",
            target_type="user",
            target_id=str(user.id),
            actor_id=user.id
        )

        return user, access_token, raw_refresh

    def refresh_session(
        self,
        db: Session,
        raw_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Executes Refresh Token Rotation (RTR).
        Detects reuse attacks; if reuse detected, invalidates all sessions for user.
        """
        if not raw_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required."
            )

        token_hash = hash_refresh_token(raw_refresh_token)
        now = datetime.datetime.utcnow()

        # Look up session by token hash
        session_record = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()
        if not session_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )

        user = db.query(User).filter(User.id == session_record.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive or does not exist."
            )

        # REUSE DETECTION!
        if session_record.is_revoked:
            # Terminate all active sessions for this user immediately
            db.query(UserSession).filter(UserSession.user_id == user.id).update({"is_revoked": True, "revoked_at": now})
            user.token_version += 1
            db.commit()

            audit_service.log_event(
                db=db,
                action="SESSION_REUSE_DETECTED",
                target_type="user",
                target_id=str(user.id),
                actor_id=user.id,
                details={"revoked_session_id": session_record.session_id}
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Security alert: Token reuse detected. All sessions terminated."
            )

        # Check expiration
        if session_record.expires_at < now:
            session_record.is_revoked = True
            session_record.revoked_at = now
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again."
            )

        # ROTATION: Revoke current session and issue replacement
        new_session_id = str(uuid.uuid4())
        new_raw_refresh, new_refresh_hash = generate_refresh_token()

        session_record.is_revoked = True
        session_record.revoked_at = now
        session_record.replaced_by_session_id = new_session_id

        new_session = UserSession(
            session_id=new_session_id,
            user_id=user.id,
            refresh_token_hash=new_refresh_hash,
            created_at=now,
            expires_at=now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            last_used_at=now,
            is_revoked=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(new_session)
        db.commit()

        new_access_token = create_access_token(user.id, user.role, user.token_version)
        return user, new_access_token, new_raw_refresh

    def logout_session(self, db: Session, raw_refresh_token: Optional[str]) -> None:
        """Revokes the active session matching the refresh token."""
        if not raw_refresh_token:
            return

        token_hash = hash_refresh_token(raw_refresh_token)
        session_record = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash).first()
        if session_record and not session_record.is_revoked:
            session_record.is_revoked = True
            session_record.revoked_at = datetime.datetime.utcnow()
            db.commit()
            audit_service.log_event(
                db=db,
                action="USER_LOGOUT",
                target_type="user",
                target_id=str(session_record.user_id),
                actor_id=session_record.user_id
            )


auth_service = AuthService()

