"""Intelligence Layer API Routes (Phase 3.1 Refinements).

Endpoints:
- POST /api/intelligence/chat        : Intelligent multilingual conversational pipeline with staged consent
- GET  /api/intelligence/facilities  : Facility search & filtering with strict verification badges
- POST /api/intelligence/incidents   : Incident creation with safety escalation and consent requirements
- GET  /api/intelligence/incidents/{id} : Incident retrieval with privacy protections
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    FacilityOutput,
    IncidentCreateRequest,
    IncidentOutput,
)
from backend.services.assistant_service import assistant_service
from backend.services.facility_service import facility_service, sanitize_facility_for_display
from backend.services.incident_service import IncidentServiceError, incident_service

logger = logging.getLogger("warkari.routes.intelligence")

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence & Retrieval"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Text Assistant Intelligence Pipeline",
    description="Processes pilgrim query with intent classification, consent workflow, and localized response."
)
async def chat_endpoint(
    payload: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    try:
        result = assistant_service.process_chat(
            db=db,
            message=payload.message,
            language=payload.language,
            user_lat=payload.latitude,
            user_lon=payload.longitude,
            location_name=payload.location_name,
            user_id=payload.user_id,
            missing_person_consent=payload.missing_person_consent,
            missing_person_details=payload.missing_person_details
        )
        return ChatResponse(**result)
    except Exception as exc:
        logger.exception("Error in /api/intelligence/chat")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process intelligence request."
        )


@router.get(
    "/facilities",
    response_model=List[FacilityOutput],
    summary="Search and filter route facilities",
    description="Search facilities by category, location, and operational/verification status. Synthetic demo facilities are never marked verified."
)
async def list_facilities_endpoint(
    category: Optional[str] = Query(None, description="drinking_water, medical, sanitation, food, resting_area, emergency"),
    location: Optional[str] = Query(None, description="Town, village or landmark search"),
    query: Optional[str] = Query(None, description="General search term"),
    language: Optional[str] = Query("mr-IN", description="Preferred language code: mr-IN, hi-IN, en-IN"),
    only_verified: bool = Query(False, description="Filter only genuinely verified facilities (excludes demo data)"),
    operational_only: bool = Query(True, description="Filter only operational facilities"),
    user_lat: Optional[float] = Query(None, description="User latitude for distance sorting"),
    user_lon: Optional[float] = Query(None, description="User longitude for distance sorting"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[FacilityOutput]:
    results = facility_service.search_facilities(
        db=db,
        category=category,
        query=query,
        location=location,
        only_verified=only_verified,
        operational_only=operational_only,
        user_lat=user_lat,
        user_lon=user_lon,
        limit=limit
    )

    formatted: List[FacilityOutput] = []
    for fac, dist in results:
        clean_dict = sanitize_facility_for_display(fac, language=language)
        clean_dict["distance_km"] = dist
        formatted.append(FacilityOutput(**clean_dict))

    return formatted


@router.post(
    "/incidents",
    response_model=IncidentOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Create assistance incident",
    description="Creates an incident with automatic priority escalation, consent validation, and safety disclaimers."
)
async def create_incident_endpoint(
    payload: IncidentCreateRequest,
    db: Session = Depends(get_db)
) -> IncidentOutput:
    if payload.category == "lost_person" and not payload.user_consent_granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit user consent is required before registering a missing person assistance request."
        )

    try:
        incident = incident_service.create_incident(
            db=db,
            category=payload.category,
            description=payload.description,
            language=payload.language,
            urgency_level=payload.urgency_level,
            location_description=payload.location_description,
            latitude=payload.latitude,
            longitude=payload.longitude,
            user_id=payload.user_id
        )

        lang = (payload.language or "mr-IN").lower()
        if lang.startswith("mr"):
            disclaimer = "आपली नोंदणी प्राप्त झाली आहे. याचा अर्थ स्वयंसेवक त्वरित नियुक्त झाला आहे किंवा आपत्कालीन सेवांशी संपर्क झाला आहे असा नाही."
        elif lang.startswith("hi"):
            disclaimer = "आपका अनुरोध दर्ज कर लिया गया है। इसका यह अर्थ नहीं है कि स्वयंसेवक नियुक्त हो गया है या आपातकालीन सेवाओं से संपर्क हो चुका है।"
        else:
            disclaimer = "Your request has been recorded. This does not mean a volunteer has been assigned or that emergency services have been contacted."

        return IncidentOutput(
            id=incident.id,
            category=incident.category,
            description=incident.description,
            urgency_level=incident.urgency_level,
            status=incident.status,
            location_description=incident.location_description,
            created_at=incident.created_at.isoformat() if incident.created_at else None,
            safety_disclaimer=disclaimer,
            public_reference=incident.public_reference,
            raw_tracking_token=getattr(incident, 'raw_tracking_token', None)
        )
    except IncidentServiceError as i_err:
        raise HTTPException(status_code=i_err.status_code, detail=i_err.message)
    except Exception as exc:
        logger.exception("Error creating incident")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record incident ticket."
        )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentOutput,
    summary="Retrieve incident status with privacy protection",
    description="Returns public status of an incident without exposing private personal details or raw messages."
)
async def get_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db)
) -> IncidentOutput:
    incident = incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident #{incident_id} not found."
        )

    # Privacy safety: Public endpoint masks personal descriptions across all incident categories
    if incident.category == "lost_person":
        sanitized_desc = "हरवलेली व्यक्ती शोध मोहीम नोंद (तपशील नियंत्रण कक्षाकडे सुरक्षित आहेत) / Missing Person Request (Details securely held by coordination desk)"
    else:
        sanitized_desc = f"साहाय्य तिकीट नोंद #{incident.id} [{incident.category}] (तपशील अधिकृत मदत पथकाकडे सुरक्षित)"

    return IncidentOutput(
        id=incident.id,
        category=incident.category,
        description=sanitized_desc,
        urgency_level=incident.urgency_level,
        status=incident.status,
        location_description=incident.location_description,
        created_at=incident.created_at.isoformat() if incident.created_at else None,
        safety_disclaimer="हे तिकीट सक्रिय आहे. आपत्कालीन परिस्थितीत थेट पालखी मदत कक्षाशी संपर्क साधा."
    )
