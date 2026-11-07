"""Incident Lifecycle, Assignment, and Public Tracking Service for Warkari."""

import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models import (
    Incident,
    IncidentAssignment,
    IncidentStatusHistory,
    VolunteerProfile,
    User
)
from backend.services.audit_service import audit_service
from backend.utils.tracking import hash_tracking_token


PUBLIC_STATUS_MESSAGES = {
    "CREATED": "आपली मदत विनंती प्राप्त झाली आहे. समन्वयक कक्षाकडून पडताळणी सुरू आहे. (Your request has been received and is being triaged.)",
    "OPEN": "आपली मदत विनंती नोंदवली गेली आहे. (Your request has been recorded.)",
    "TRIAGED": "विनंतीची पडताळणी पूर्ण झाली आहे. मदत पथक समन्वय सुरू आहे. (Request triaged; coordinating assistance team.)",
    "ASSIGNED": "स्वयंसेवक नियुक्त करण्यात आला आहे. स्वयंसेवकाच्या स्वीकृतीची प्रतीक्षा आहे. (Volunteer has been assigned; awaiting confirmation.)",
    "ACKNOWLEDGED": "स्वयंसेवकाने विनंती स्वीकारली आहे आणि तयारी करत आहेत. (Volunteer accepted request and is preparing.)",
    "EN_ROUTE": "स्वयंसेवक आपल्या स्थानाकडे रवाना झाले आहेत. कृपया सुरक्षित ठिकाणी थांबा. (Volunteer is en route to your location. Please stay safe.)",
    "ON_SCENE": "स्वयंसेवक घटनास्थळी पोहोचले असून मदत कार्य सुरू आहे. (Volunteer has arrived on scene and is actively assisting.)",
    "RESOLVED": "मदत कार्य यशस्वीरीत्या पूर्ण झाले आहे. (Assistance has been marked resolved.)",
    "CLOSED": "हे तिकीट प्रशासकीयदृष्ट्या पूर्ण करून बंद केले आहे. (Ticket administratively closed.)",
    "CANCELLED": "ही विनंती रद्द करण्यात आली आहे. (This request has been cancelled.)",
}


class IncidentWorkflowService:
    def assign_volunteer(
        self,
        db: Session,
        incident_id: int,
        volunteer_profile_id: int,
        coordinator_id: int,
        notes: Optional[str] = None
    ) -> IncidentAssignment:
        """
        Assigns an approved volunteer to an incident.
        Enforces:
        - Incident must exist and not be CLOSED or CANCELLED.
        - Volunteer profile must exist, have approval_status == 'APPROVED', and user must be active.
        - Prevents conflicting active assignments (status IN ('PENDING', 'ACCEPTED')).
        - Sets incident_assignments status to 'PENDING'.
        - Does NOT claim dispatch; updates incident status to 'ASSIGNED'.
        - Updates status history and audit logs.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")

        if incident.status in ["CLOSED", "CANCELLED"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot assign volunteer to an incident in '{incident.status}' status."
            )

        # Check existing active assignment
        active_assignment = db.query(IncidentAssignment).filter(
            IncidentAssignment.incident_id == incident.id,
            IncidentAssignment.status.in_(["PENDING", "ACCEPTED"])
        ).first()
        if active_assignment:
            raise HTTPException(
                status_code=409,
                detail="Incident already has an active or pending volunteer assignment. Reassign or cancel current assignment first."
            )

        vol_profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == volunteer_profile_id).first()
        if not vol_profile:
            raise HTTPException(status_code=404, detail="Volunteer profile not found.")

        if vol_profile.approval_status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail="Volunteer is not approved. Only APPROVED volunteers can be assigned."
            )

        vol_user = db.query(User).filter(User.id == vol_profile.user_id).first()
        if not vol_user or not vol_user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Volunteer user account is inactive or suspended."
            )

        now = datetime.datetime.utcnow()

        # Create authoritative assignment record
        assignment = IncidentAssignment(
            incident_id=incident.id,
            volunteer_profile_id=vol_profile.id,
            assigned_by=coordinator_id,
            status="PENDING",
            assigned_at=now
        )
        db.add(assignment)

        # Record Status History
        prev_status = incident.status
        incident.status = "ASSIGNED"
        incident.updated_at = now
        # Legacy pointer remains NULL during PENDING to avoid false claim of acceptance
        incident.assigned_volunteer_id = None

        history_entry = IncidentStatusHistory(
            incident_id=incident.id,
            previous_status=prev_status,
            new_status="ASSIGNED",
            changed_by=coordinator_id,
            timestamp=now,
            reason=f"Volunteer #{vol_profile.id} designated by coordinator #{coordinator_id}. Awaiting volunteer acceptance."
        )
        db.add(history_entry)

        db.commit()
        db.refresh(assignment)

        audit_service.log_event(
            db=db,
            action="INCIDENT_ASSIGNMENT_CREATED",
            target_type="incident",
            target_id=str(incident.id),
            actor_id=coordinator_id,
            details={"volunteer_profile_id": vol_profile.id, "assignment_id": assignment.id}
        )

        return assignment

    def volunteer_respond_assignment(
        self,
        db: Session,
        assignment_id: int,
        volunteer_user_id: int,
        action: str,  # "ACCEPT" or "REJECT"
        rejection_reason: Optional[str] = None
    ) -> IncidentAssignment:
        """
        Assigned volunteer explicitly accepts or rejects an assignment.
        """
        assignment = db.query(IncidentAssignment).filter(IncidentAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found.")

        vol_profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == assignment.volunteer_profile_id).first()
        if not vol_profile or vol_profile.user_id != volunteer_user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You can only respond to assignments designating your own volunteer profile."
            )

        if assignment.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail=f"Assignment is in '{assignment.status}' state and cannot be accepted/rejected."
            )

        now = datetime.datetime.utcnow()
        incident = db.query(Incident).filter(Incident.id == assignment.incident_id).first()
        prev_status = incident.status

        if action.upper() == "ACCEPT":
            assignment.status = "ACCEPTED"
            assignment.accepted_at = now
            incident.status = "ACKNOWLEDGED"
            incident.updated_at = now
            # Synchronize legacy pointer now that assignment is verified accepted
            incident.assigned_volunteer_id = vol_profile.legacy_volunteer_id

            history = IncidentStatusHistory(
                incident_id=incident.id,
                previous_status=prev_status,
                new_status="ACKNOWLEDGED",
                changed_by=volunteer_user_id,
                timestamp=now,
                reason="Volunteer accepted assignment and acknowledged responsibility."
            )
            db.add(history)
            audit_action = "ASSIGNMENT_ACCEPTED"

        elif action.upper() == "REJECT":
            if not rejection_reason or len(rejection_reason.strip()) < 5:
                raise HTTPException(
                    status_code=422,
                    detail="A valid rejection reason (minimum 5 characters) is required."
                )
            assignment.status = "REJECTED"
            assignment.rejected_at = now
            assignment.rejection_reason = rejection_reason.strip()
            
            # Revert incident to TRIAGED/OPEN so coordinator pool can reassign
            incident.status = "TRIAGED"
            incident.updated_at = now
            incident.assigned_volunteer_id = None

            history = IncidentStatusHistory(
                incident_id=incident.id,
                previous_status=prev_status,
                new_status="TRIAGED",
                changed_by=volunteer_user_id,
                timestamp=now,
                reason=f"Volunteer rejected assignment: {rejection_reason.strip()}"
            )
            db.add(history)
            audit_action = "ASSIGNMENT_REJECTED"
        else:
            raise HTTPException(status_code=400, detail="Action must be ACCEPT or REJECT.")

        db.commit()
        db.refresh(assignment)

        audit_service.log_event(
            db=db,
            action=audit_action,
            target_type="incident",
            target_id=str(incident.id),
            actor_id=volunteer_user_id,
            details={"assignment_id": assignment.id}
        )

        return assignment

    def volunteer_update_progress(
        self,
        db: Session,
        incident_id: int,
        volunteer_user_id: int,
        target_status: str,  # EN_ROUTE, ON_SCENE, RESOLVED
        notes: Optional[str] = None
    ) -> Incident:
        """
        Assigned volunteer reports transit progress: EN_ROUTE -> ON_SCENE -> RESOLVED.
        Strict server-side validation against state transition matrix.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")

        # Find active accepted assignment
        active_assignment = db.query(IncidentAssignment).filter(
            IncidentAssignment.incident_id == incident.id,
            IncidentAssignment.status == "ACCEPTED"
        ).first()

        if not active_assignment:
            raise HTTPException(
                status_code=400,
                detail="Incident does not have an active accepted assignment."
            )

        vol_profile = db.query(VolunteerProfile).filter(VolunteerProfile.id == active_assignment.volunteer_profile_id).first()
        if not vol_profile or vol_profile.user_id != volunteer_user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: You are not the assigned volunteer for this incident."
            )

        target = target_status.upper().strip()
        current = incident.status

        # Transition matrix enforcement
        valid_transitions = {
            "ACKNOWLEDGED": ["EN_ROUTE"],
            "EN_ROUTE": ["ON_SCENE"],
            "ON_SCENE": ["RESOLVED"]
        }

        allowed = valid_transitions.get(current, [])
        if target not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid lifecycle transition from '{current}' to '{target}'. Allowed next state: {allowed}."
            )

        now = datetime.datetime.utcnow()
        prev_status = incident.status
        incident.status = target
        incident.updated_at = now

        if target == "RESOLVED":
            active_assignment.status = "COMPLETED"
            active_assignment.completed_at = now

        history = IncidentStatusHistory(
            incident_id=incident.id,
            previous_status=prev_status,
            new_status=target,
            changed_by=volunteer_user_id,
            timestamp=now,
            reason=notes or f"Volunteer reported status change: {target}"
        )
        db.add(history)
        db.commit()
        db.refresh(incident)

        audit_service.log_event(
            db=db,
            action=f"INCIDENT_TRANSITION_{target}",
            target_type="incident",
            target_id=str(incident.id),
            actor_id=volunteer_user_id,
            details={"from": prev_status, "to": target}
        )

        return incident

    def public_track_incident(self, db: Session, raw_token: str) -> dict:
        """
        Public lookup by private 256-bit tracking token.
        Zero exposure of sequential integer ID, personal details, or coordinator notes.
        """
        token_hash = hash_tracking_token(raw_token)
        incident = db.query(Incident).filter(Incident.tracking_token_hash == token_hash).first()

        if not incident:
            # Neutral error message prevents token probing
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No incident found matching this tracking token. Please check and re-enter your private token."
            )

        status_msg = PUBLIC_STATUS_MESSAGES.get(
            incident.status,
            "आपल्या विनंतीवर आवश्यक कार्यवाही सुरू आहे. (Action is in progress on your request.)"
        )

        return {
            "public_reference": incident.public_reference or "WKR-PENDING",
            "category": incident.category,
            "status": incident.status,
            "created_at": incident.created_at.isoformat() if incident.created_at else "",
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else "",
            "status_message": status_msg
        }


incident_workflow_service = IncidentWorkflowService()

