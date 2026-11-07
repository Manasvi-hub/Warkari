"""Secure Administrator Bootstrap CLI Command.

Usage:
    python -m backend.cli.bootstrap_admin
"""

import sys
import getpass
import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import User
from backend.utils.security import hash_password
from backend.services.audit_service import audit_service


def bootstrap_admin():
    db: Session = SessionLocal()
    try:
        print("=== WARKARI SECURE ADMINISTRATOR BOOTSTRAP ===")
        
        # Check if an administrator already exists
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            print(f"[SECURITY ALERT] An administrator already exists (User #{existing_admin.id}: {existing_admin.name}).")
            print("To prevent unauthorized duplicate bootstrap, aborting.")
            sys.exit(1)

        name = input("Enter Administrator Full Name: ").strip()
        if not name:
            print("Error: Name cannot be empty.")
            sys.exit(1)

        phone = input("Enter Administrator Phone (+91XXXXXXXXXX): ").strip()
        if len(phone) < 10:
            print("Error: Invalid phone number.")
            sys.exit(1)

        # Check if phone already registered
        existing_user = db.query(User).filter(User.phone == phone).first()
        if existing_user:
            print(f"Error: A user with phone {phone} already exists.")
            sys.exit(1)

        email = input("Enter Administrator Email (optional): ").strip() or None

        password = getpass.getpass("Enter Secure Password (min 8 chars): ").strip()
        if len(password) < 8:
            print("Error: Password must be at least 8 characters long.")
            sys.exit(1)

        confirm_password = getpass.getpass("Confirm Password: ").strip()
        if password != confirm_password:
            print("Error: Passwords do not match.")
            sys.exit(1)

        # Hash and persist
        hashed = hash_password(password)
        admin_user = User(
            name=name,
            phone=phone,
            email=email,
            hashed_password=hashed,
            role="admin",
            preferred_language="mr",
            token_version=1,
            is_active=True,
            is_phone_verified=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        audit_service.log_event(
            db=db,
            action="BOOTSTRAP_ADMIN_CREATED",
            target_type="user",
            target_id=str(admin_user.id),
            actor_id=admin_user.id
        )

        print(f"\n[SUCCESS] Administrator account successfully created!")
        print(f"ID: {admin_user.id} | Name: {admin_user.name} | Phone: {admin_user.phone} | Role: admin")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Bootstrap failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_admin()

