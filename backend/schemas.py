from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------
# System & Health Schemas
# -------------------------------------------------------------
class RootResponse(BaseModel):
    project: str = "Warkari"
    message: str = "Welcome to Warkari API"
    status: str = "running"


class HealthResponse(BaseModel):
    status: str = "healthy"


class SystemServiceStatus(BaseModel):
    database: str
    gnani_stt_service: str
    gnani_tts_service: str


class SystemInfoResponse(BaseModel):
    project: str
    version: str
    environment: str
    status: str
    services: SystemServiceStatus


# -------------------------------------------------------------
# Assistant & Voice Schemas (Phase 2)
# -------------------------------------------------------------
class TranscribeResponse(BaseModel):
    success: bool
    transcript: str
    language: str
    detected_language: Optional[str] = None
    model: str = "prisma-v2.5"
    request_id: Optional[str] = None


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into speech")
    language: str = Field("mr-IN", description="Language code: mr-IN, hi-IN, or en-IN")
    voice: Optional[str] = Field(None, description="Voice name from Gnani Timbre catalog")
    speed: Optional[float] = Field(1.0, ge=0.85, le=1.15, description="Playback speed (0.85 - 1.15)")


class VoiceInteractionResponse(BaseModel):
    success: bool
    transcript: str
    language: str
    detected_language: Optional[str] = None
    response_text: str
    speech_text: Optional[str] = Field(None, description="Normalized spoken text sent to Gnani Timbre TTS")
    intent: Optional[str] = None
    confidence: Optional[float] = None
    facilities: List["FacilityOutput"] = []
    incident: Optional["IncidentOutput"] = None
    ticket_id: Optional[int] = None
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None


# -------------------------------------------------------------
# Intelligence Layer Schemas (Phase 3 & 3.1)
# -------------------------------------------------------------
class FacilityOutput(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    operational_status: str
    is_verified: bool
    is_demo: bool
    display_status: str = "UNVERIFIED"  # "DEMO DATA" | "VERIFIED" | "UNVERIFIED"
    source: Optional[str] = None
    contact_phone: Optional[str] = None
    last_verified_at: Optional[str] = None

    # Multilingual & Fallback Metadata (Phase 3.3.5)
    requested_language: Optional[str] = "mr"
    resolved_language: Optional[str] = "mr"
    language_fallback: bool = False
    name_fallback: bool = False
    location_fallback: bool = False
    description_fallback: bool = False

    # Optional granular multilingual fields (exposed only if approved/populated)
    name_en: Optional[str] = None
    name_hi: Optional[str] = None
    location_en: Optional[str] = None
    location_hi: Optional[str] = None
    description_en: Optional[str] = None
    description_hi: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentOutput(BaseModel):
    id: int
    category: str
    description: str
    urgency_level: str
    status: str
    location_description: Optional[str] = None
    created_at: Optional[str] = None
    safety_disclaimer: Optional[str] = None
    public_reference: Optional[str] = None
    raw_tracking_token: Optional[str] = Field(None, description="Ephemeral raw tracking token returned once upon creation")

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pilgrim request in text form")
    language: str = Field("mr-IN", description="Preferred language code: mr-IN, hi-IN, en-IN")
    latitude: Optional[float] = Field(None, description="Optional GPS latitude")
    longitude: Optional[float] = Field(None, description="Optional GPS longitude")
    location_name: Optional[str] = Field(None, description="Optional textual locality name or landmark")
    user_id: Optional[int] = Field(None, description="Optional user ID")
    # Missing person consent workflow fields
    missing_person_consent: Optional[bool] = Field(
        None,
        description="Explicit user consent to register a missing person assistance request"
    )
    missing_person_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured minimal details for missing person coordination (name, age, last_seen)"
    )


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response_text: str
    speech_text: Optional[str] = Field(None, description="Normalized spoken text corresponding to response_text")
    facilities: List[FacilityOutput] = []
    incident: Optional[IncidentOutput] = None
    clarification_required: bool = False
    awaiting_missing_person_consent: bool = False
    awaiting_missing_person_details: bool = False


class IncidentCreateRequest(BaseModel):
    category: str = Field(..., description="medical_emergency, water_shortage, food_shortage, sanitation_issue, lost_person, general_assistance, other")
    description: str = Field(..., min_length=5, description="Detailed description of assistance needed")
    language: str = Field("mr-IN", description="mr-IN, hi-IN, en-IN")
    urgency_level: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    location_description: Optional[str] = Field(None, description="Landmark, route KM or village")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: Optional[int] = None
    # Consent confirmation for sensitive categories like lost_person
    user_consent_granted: bool = Field(
        True,
        description="Explicit user consent confirmation for recording assistance request"
    )


# -------------------------------------------------------------
# Public Incident Tracking Schemas (Phase 4.3)
# -------------------------------------------------------------
class PublicTrackRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=128, description="User-provided private tracking token")


class PublicTrackResponse(BaseModel):
    public_reference: str
    category: str
    status: str
    created_at: str
    updated_at: str
    status_message: str


# -------------------------------------------------------------
# Coordinator & Volunteer Incident Management Schemas (Phase 4.3)
# -------------------------------------------------------------
class IncidentAssignmentCreateRequest(BaseModel):
    volunteer_profile_id: int
    notes: Optional[str] = Field(None, max_length=500)


class IncidentRejectionRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory explanation for assignment rejection")


class IncidentTransitionRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class IncidentAssignmentOutput(BaseModel):
    id: int
    incident_id: int
    volunteer_profile_id: int
    assigned_by: int
    status: str
    assigned_at: str
    accepted_at: Optional[str] = None
    rejected_at: Optional[str] = None
    completed_at: Optional[str] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailOutput(BaseModel):
    id: int
    public_reference: Optional[str] = None
    category: str
    description: str
    urgency_level: str
    priority: str
    status: str
    location_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: str
    updated_at: str
    assigned_volunteer_id: Optional[int] = None
    active_assignment: Optional[IncidentAssignmentOutput] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedIncidentList(BaseModel):
    total: int
    page: int
    limit: int
    items: List[IncidentDetailOutput]


# -------------------------------------------------------------
# User & Authentication Schemas (Phase 4.2)
# -------------------------------------------------------------
class UserBase(BaseModel):
    name: str = Field(..., max_length=120)
    preferred_language: str = Field("mr", max_length=30)
    role: str = Field("pilgrim", max_length=50)


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20, description="Mobile number")
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters")
    email: Optional[str] = Field(None, max_length=150)
    preferred_language: Optional[str] = Field("mr", max_length=30)
    requested_role: str = Field("pilgrim", description="Permitted public values: 'pilgrim' or 'volunteer'")
    skills: Optional[str] = Field(None, description="Optional skills or certifications for volunteers")
    sector: Optional[str] = Field(None, description="Preferred assignment sector for volunteers")


class UserLoginRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=30)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Optional refresh token in body if not sent via cookie")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user_id: int
    name: str
    role: str
    refresh_token: Optional[str] = None  # Returned for clients unable to use cookies


class UserProfileResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    preferred_language: str
    is_active: bool
    is_phone_verified: bool
    created_at: datetime
    volunteer_status: Optional[str] = None
    volunteer_sector: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VolunteerApprovalRequest(BaseModel):
    approval_status: str = Field(..., description="APPROVED, REJECTED, or SUSPENDED")
    sector: Optional[str] = Field(None, description="Assigned sector on approval")


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="pilgrim, volunteer, coordinator, admin")


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Facility Schemas
# -------------------------------------------------------------
class FacilityBase(BaseModel):
    name: str
    category: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operational_status: str = "operational"
    source: Optional[str] = "administration"


class FacilityCreate(FacilityBase):
    pass


class FacilityRead(FacilityBase):
    id: int
    last_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Incident Schemas
# -------------------------------------------------------------
class IncidentBase(BaseModel):
    category: str
    description: str
    priority: str = "medium"
    status: str = "reported"


class IncidentCreate(IncidentBase):
    user_id: Optional[int] = None


class IncidentRead(IncidentBase):
    id: int
    user_id: Optional[int] = None
    assigned_volunteer_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Volunteer Schemas
# -------------------------------------------------------------
class VolunteerBase(BaseModel):
    name: str
    phone: str
    assigned_area: Optional[str] = None
    availability: str = "available"


class VolunteerCreate(VolunteerBase):
    pass


class VolunteerRead(VolunteerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
