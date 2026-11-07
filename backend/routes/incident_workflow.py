"""Incident Operations and Volunteer Workflow API Routes (Phase 4.3)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Incident,
    IncidentAssignment,
    VolunteerProfile,
    User
)
from backend.schemas import (
    PublicTrackRequest,
    PublicTrackResponse,
    IncidentAssignmentCreateRequest,
    IncidentRejectionRequest,
    IncidentTransitionRequest,
    IncidentAssignmentOutput,
    IncidentDetailOutput,
    PaginatedIncidentList
)
from backend.services.incident_workflow_service import incident_workflow_service
from backend.dependencies.auth import (
    require_coordinator,
    require_approved_volunteer,
    get_current_user
)
from backend.utils.rate_limit import rate_limit_public_tracking

router = APIRouter(tags=["Incident Operations & Public Tracking"])


# -------------------------------------------------------------
# 1. Public Incident Tracking
# -------------------------------------------------------------
@router.post(
    "/api/v1/public/incidents/track",
    response_model=PublicTrackResponse,
    summary="Public tracking by private 256-bit token",
    dependencies=[Depends(rate_limit_public_tracking)]
)
async def public_track_endpoint(
    payload: PublicTrackRequest,
    db: Session = Depends(get_db)
):
    """
    Public lookup by private token.
    - Rate limited to 10 requests per minute per IP.
    - Zero exposure of internal incident ID, PII, volunteer contact, or notes.
    """
    result = incident_workflow_service.public_track_incident(db, payload.token)
    return PublicTrackResponse(**result)


# -------------------------------------------------------------
# 2. Coordinator Incident Management Endpoints
# -------------------------------------------------------------
@router.get(
    "/api/v1/coordinator/incidents",
    response_model=PaginatedIncidentList,
    summary="List incidents with filtering and pagination"
)
async def list_incidents_coordinator(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    coordinator: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)

    if category:
        query = query.filter(Incident.category == category.lower())
    if status:
        query = query.filter(Incident.status == status.upper())
    if sector:
        query = query.filter(Incident.location_description.ilike(f"%{sector}%"))

    total = query.count()
    offset = (page - 1) * limit
    incidents = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for inc in incidents:
        active_assign = db.query(IncidentAssignment).filter(
            IncidentAssignment.incident_id == inc.id,
            IncidentAssignment.status.in_(["PENDING", "ACCEPTED"])
        ).first()

        assign_out = None
        if active_assign:
            assign_out = IncidentAssignmentOutput(
                id=active_assign.id,
                incident_id=active_assign.incident_id,
                volunteer_profile_id=active_assign.volunteer_profile_id,
                assigned_by=active_assign.assigned_by,
                status=active_assign.status,
                assigned_at=active_assign.assigned_at.isoformat(),
                accepted_at=active_assign.accepted_at.isoformat() if active_assign.accepted_at else None,
                rejected_at=active_assign.rejected_at.isoformat() if active_assign.rejected_at else None,
                completed_at=active_assign.completed_at.isoformat() if active_assign.completed_at else None,
                rejection_reason=active_assign.rejection_reason
            )

        items.append(IncidentDetailOutput(
            id=inc.id,
            public_reference=inc.public_reference,
            category=inc.category,
            description=inc.description,
            urgency_level=inc.urgency_level,
            priority=inc.priority,
            status=inc.status,
            location_description=inc.location_description,
            latitude=inc.latitude,
            longitude=inc.longitude,
            created_at=inc.created_at.isoformat() if inc.created_at else "",
            updated_at=inc.updated_at.isoformat() if inc.updated_at else "",
            assigned_volunteer_id=inc.assigned_volunteer_id,
            active_assignment=assign_out
        ))

    return PaginatedIncidentList(total=total, page=page, limit=limit, items=items)


@router.get(
    "/api/v1/coordinator/eligible-volunteers",
    summary="List approved volunteers eligible for assignment"
)
async def list_eligible_volunteers(
    sector: Optional[str] = Query(None),
    coordinator: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    query = db.query(VolunteerProfile).filter(VolunteerProfile.approval_status == "APPROVED")
    if sector:
        query = query.filter(VolunteerProfile.sector.ilike(f"%{sector}%"))
    profiles = query.all()

    result = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user and user.is_active:
            result.append({
                "profile_id": p.id,
                "user_id": user.id,
                "name": user.name,
                "phone": user.phone,
                "sector": p.sector,
                "skills": p.skills,
                "availability": p.availability,
                "approval_status": p.approval_status
            })
    return result


@router.post(
    "/api/v1/coordinator/incidents/{incident_id}/assign",
    response_model=IncidentAssignmentOutput,
    summary="Assign an approved volunteer to an incident"
)
async def assign_volunteer_endpoint(
    incident_id: int,
    payload: IncidentAssignmentCreateRequest,
    coordinator: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    assignment = incident_workflow_service.assign_volunteer(
        db=db,
        incident_id=incident_id,
        volunteer_profile_id=payload.volunteer_profile_id,
        coordinator_id=coordinator.id,
        notes=payload.notes
    )

    return IncidentAssignmentOutput(
        id=assignment.id,
        incident_id=assignment.incident_id,
        volunteer_profile_id=assignment.volunteer_profile_id,
        assigned_by=assignment.assigned_by,
        status=assignment.status,
        assigned_at=assignment.assigned_at.isoformat(),
        accepted_at=assignment.accepted_at.isoformat() if assignment.accepted_at else None,
        rejected_at=assignment.rejected_at.isoformat() if assignment.rejected_at else None,
        completed_at=assignment.completed_at.isoformat() if assignment.completed_at else None,
        rejection_reason=assignment.rejection_reason
    )


@router.get(
    "/api/v1/coordinator/incidents/{incident_id}/assignments",
    response_model=List[IncidentAssignmentOutput],
    summary="View complete assignment history for an incident"
)
async def view_assignment_history(
    incident_id: int,
    coordinator: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    assignments = db.query(IncidentAssignment).filter(
        IncidentAssignment.incident_id == incident_id
    ).order_by(IncidentAssignment.assigned_at.desc()).all()

    return [
        IncidentAssignmentOutput(
            id=a.id,
            incident_id=a.incident_id,
            volunteer_profile_id=a.volunteer_profile_id,
            assigned_by=a.assigned_by,
            status=a.status,
            assigned_at=a.assigned_at.isoformat(),
            accepted_at=a.accepted_at.isoformat() if a.accepted_at else None,
            rejected_at=a.rejected_at.isoformat() if a.rejected_at else None,
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
            rejection_reason=a.rejection_reason
        )
        for a in assignments
    ]


# -------------------------------------------------------------
# 3. Volunteer Workflow Endpoints
# -------------------------------------------------------------
@router.get(
    "/api/v1/volunteer/assignments",
    response_model=List[IncidentAssignmentOutput],
    summary="List all assignments designating the current volunteer"
)
async def list_volunteer_assignments(
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == volunteer_user.id).first()
    if not profile:
        return []

    assignments = db.query(IncidentAssignment).filter(
        IncidentAssignment.volunteer_profile_id == profile.id
    ).order_by(IncidentAssignment.assigned_at.desc()).all()

    return [
        IncidentAssignmentOutput(
            id=a.id,
            incident_id=a.incident_id,
            volunteer_profile_id=a.volunteer_profile_id,
            assigned_by=a.assigned_by,
            status=a.status,
            assigned_at=a.assigned_at.isoformat(),
            accepted_at=a.accepted_at.isoformat() if a.accepted_at else None,
            rejected_at=a.rejected_at.isoformat() if a.rejected_at else None,
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
            rejection_reason=a.rejection_reason
        )
        for a in assignments
    ]


@router.post(
    "/api/v1/volunteer/assignments/{assignment_id}/accept",
    response_model=IncidentAssignmentOutput,
    summary="Volunteer accepts assigned request"
)
async def accept_assignment_endpoint(
    assignment_id: int,
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    assignment = incident_workflow_service.volunteer_respond_assignment(
        db=db,
        assignment_id=assignment_id,
        volunteer_user_id=volunteer_user.id,
        action="ACCEPT"
    )

    return IncidentAssignmentOutput(
        id=assignment.id,
        incident_id=assignment.incident_id,
        volunteer_profile_id=assignment.volunteer_profile_id,
        assigned_by=assignment.assigned_by,
        status=assignment.status,
        assigned_at=assignment.assigned_at.isoformat(),
        accepted_at=assignment.accepted_at.isoformat() if assignment.accepted_at else None,
        rejected_at=assignment.rejected_at.isoformat() if assignment.rejected_at else None,
        completed_at=assignment.completed_at.isoformat() if assignment.completed_at else None,
        rejection_reason=assignment.rejection_reason
    )


@router.post(
    "/api/v1/volunteer/assignments/{assignment_id}/reject",
    response_model=IncidentAssignmentOutput,
    summary="Volunteer rejects assigned request with mandatory reason"
)
async def reject_assignment_endpoint(
    assignment_id: int,
    payload: IncidentRejectionRequest,
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    assignment = incident_workflow_service.volunteer_respond_assignment(
        db=db,
        assignment_id=assignment_id,
        volunteer_user_id=volunteer_user.id,
        action="REJECT",
        rejection_reason=payload.reason
    )

    return IncidentAssignmentOutput(
        id=assignment.id,
        incident_id=assignment.incident_id,
        volunteer_profile_id=assignment.volunteer_profile_id,
        assigned_by=assignment.assigned_by,
        status=assignment.status,
        assigned_at=assignment.assigned_at.isoformat(),
        accepted_at=assignment.accepted_at.isoformat() if assignment.accepted_at else None,
        rejected_at=assignment.rejected_at.isoformat() if assignment.rejected_at else None,
        completed_at=assignment.completed_at.isoformat() if assignment.completed_at else None,
        rejection_reason=assignment.rejection_reason
    )


@router.post(
    "/api/v1/volunteer/incidents/{incident_id}/en-route",
    summary="Volunteer marks status EN_ROUTE"
)
async def mark_en_route(
    incident_id: int,
    payload: Optional[IncidentTransitionRequest] = None,
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    incident = incident_workflow_service.volunteer_update_progress(
        db=db,
        incident_id=incident_id,
        volunteer_user_id=volunteer_user.id,
        target_status="EN_ROUTE",
        notes=payload.notes if payload else None
    )
    return {"message": "Incident marked EN_ROUTE.", "status": incident.status}


@router.post(
    "/api/v1/volunteer/incidents/{incident_id}/on-scene",
    summary="Volunteer marks status ON_SCENE"
)
async def mark_on_scene(
    incident_id: int,
    payload: Optional[IncidentTransitionRequest] = None,
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    incident = incident_workflow_service.volunteer_update_progress(
        db=db,
        incident_id=incident_id,
        volunteer_user_id=volunteer_user.id,
        target_status="ON_SCENE",
        notes=payload.notes if payload else None
    )
    return {"message": "Volunteer reported arrival ON_SCENE.", "status": incident.status}


@router.post(
    "/api/v1/volunteer/incidents/{incident_id}/resolve",
    summary="Volunteer marks assistance RESOLVED"
)
async def mark_resolved(
    incident_id: int,
    payload: Optional[IncidentTransitionRequest] = None,
    volunteer_user: User = Depends(require_approved_volunteer),
    db: Session = Depends(get_db)
):
    incident = incident_workflow_service.volunteer_update_progress(
        db=db,
        incident_id=incident_id,
        volunteer_user_id=volunteer_user.id,
        target_status="RESOLVED",
        notes=payload.notes if payload else None
    )
    return {"message": "Assistance marked RESOLVED.", "status": incident.status}

