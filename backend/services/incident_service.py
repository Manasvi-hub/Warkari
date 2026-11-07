"""Incident Management Service for Warkari Pilgrimage Platform.

Operates over the SQLite `incidents` table.
Handles incident creation with safety guards, urgency assignment,
and sanitized retrieval respecting privacy boundaries.

Safety & Privacy Requirements:
- Missing-person information is sensitive: never exposed through public unauthenticated endpoints.
- Incident creation does not guarantee immediate physical volunteer attendance.
- Medical emergency and immediate danger requests receive high priority.
"""

import datetime
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.models import Incident
from backend.utils.tracking import generate_tracking_credentials

logger = logging.getLogger("warkari.services.incident")

VALID_CATEGORIES = {
    "medical_emergency",
    "water_shortage",
    "food_shortage",
    "sanitation_issue",
    "lost_person",
    "general_assistance",
    "other",
}

VALID_STATUSES = {
    "OPEN",
    "ACKNOWLEDGED",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
}

VALID_URGENCIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


class IncidentServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IncidentService:
    def create_incident(
        self,
        db: Session,
        category: str,
        description: str,
        original_message: Optional[str] = None,
        language: str = "mr-IN",
        urgency_level: str = "MEDIUM",
        location_description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        user_id: Optional[int] = None
    ) -> Incident:
        """Validates and persists a pilgrim assistance incident."""
        clean_cat = (category or "").strip().lower()
        if clean_cat not in VALID_CATEGORIES:
            raise IncidentServiceError(
                f"Invalid incident category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
                status_code=422
            )

        clean_desc = (description or "").strip()
        if len(clean_desc) < 5:
            raise IncidentServiceError("Incident description must be at least 5 characters long.", status_code=422)

        clean_urgency = (urgency_level or "MEDIUM").strip().upper()
        if clean_urgency not in VALID_URGENCIES:
            clean_urgency = "MEDIUM"

        # Automated safety elevation
        if clean_cat == "medical_emergency" and clean_urgency in ["LOW", "MEDIUM"]:
            clean_urgency = "HIGH"
        elif clean_cat == "lost_person" and clean_urgency in ["LOW"]:
            clean_urgency = "MEDIUM"

        priority_map = {
            "LOW": "low",
            "MEDIUM": "medium",
            "HIGH": "high",
            "CRITICAL": "critical",
        }
        priority_val = priority_map.get(clean_urgency, "medium")

        # Generate cryptographic tracking token & non-sequential public reference
        raw_token, token_hash, public_ref = generate_tracking_credentials()

        incident = Incident(
            category=clean_cat,
            description=clean_desc,
            original_message=original_message or clean_desc,
            language=language,
            urgency_level=clean_urgency,
            priority=priority_val,
            status="OPEN",
            location_description=location_description,
            latitude=latitude,
            longitude=longitude,
            user_id=user_id,
            tracking_token_hash=token_hash,
            public_reference=public_ref,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        # Attach ephemeral raw tracking token so caller can display it once to the pilgrim
        incident.raw_tracking_token = raw_token

        # Log safely without broadcasting private PII or raw token
        logger.info("Created incident #%s [Ref: %s, Category: %s, Urgency: %s]", incident.id, incident.public_reference, incident.category, incident.urgency_level)
        return incident

    def get_incident_by_id(self, db: Session, incident_id: int) -> Optional[Incident]:
        """Retrieves incident by ID."""
        return db.query(Incident).filter(Incident.id == incident_id).first()


incident_service = IncidentService()
