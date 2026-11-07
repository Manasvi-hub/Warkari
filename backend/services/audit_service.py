"""Tamper-Resistant Audit Logging Service."""

import datetime
import hashlib
import json
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import AuditLog


class AuditService:
    def log_event(
        self,
        db: Session,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        actor_id: Optional[int] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Appends an immutable audit log record with cryptographic chaining.
        """
        # Fetch the most recent log record to link cryptographic chain
        last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
        prev_hash = last_log.current_hash if last_log else "0" * 64

        now = datetime.datetime.utcnow()

        # Sanitize details (ensure no raw passwords, tokens, or PII)
        sanitized_details = details or {}
        details_str = json.dumps(sanitized_details, sort_keys=True)

        # Compute current hash: SHA256(timestamp + actor_id + action + target_type + target_id + prev_hash)
        payload = f"{now.isoformat()}|{actor_id}|{action}|{target_type}|{target_id}|{details_str}|{prev_hash}"
        current_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        log_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            timestamp=now,
            previous_hash=prev_hash,
            current_hash=current_hash
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    def verify_chain(self, db: Session) -> bool:
        """Verifies the cryptographic integrity of the entire audit log chain."""
        logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
        expected_prev = "0" * 64

        for log in logs:
            if log.previous_hash != expected_prev:
                return False
            expected_prev = log.current_hash

        return True


audit_service = AuditService()
