import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    preferred_language = Column(String(30), nullable=False, default="mr")  # Marathi default
    role = Column(String(50), nullable=False, default="pilgrim")  # pilgrim, volunteer, coordinator, admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Phase 4.1 additions
    phone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    token_version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    is_phone_verified = Column(Boolean, nullable=False, default=False)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="user")
    volunteer_profile = relationship("VolunteerProfile", back_populates="user", uselist=False)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    transcript = Column(Text, nullable=True)  # Input voice transcript or user text
    response = Column(Text, nullable=True)    # AI or system generated response
    intent = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, intent='{self.intent}')>"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    # Canonical Marathi fields
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(80), nullable=False, index=True)  # drinking_water, medical, sanitation, food, resting_area, emergency
    description = Column(Text, nullable=True)                  # Detailed facility description/guidance
    location = Column(String(255), nullable=True)             # Human readable location/landmark

    # Approved multilingual extension columns (nullable, populated only upon human review)
    name_en = Column(String(150), nullable=True)
    name_hi = Column(String(150), nullable=True)
    location_en = Column(String(255), nullable=True)
    location_hi = Column(String(255), nullable=True)
    description_en = Column(Text, nullable=True)
    description_hi = Column(Text, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    contact_phone = Column(String(50), nullable=True)         # Verified helpline/station contact
    operational_status = Column(String(50), nullable=False, default="operational")  # operational, limited, closed
    is_verified = Column(Boolean, nullable=False, default=False, index=True)       # Verification flag
    source = Column(String(100), nullable=True, default="administration")           # official, administration, crowd
    last_verified_at = Column(DateTime, nullable=True)
    is_demo = Column(Boolean, nullable=False, default=False)                       # Demo-data indicator

    __table_args__ = (
        Index("idx_facility_lat_lng", "latitude", "longitude"),
        Index("idx_facility_cat_verified", "category", "is_verified"),
    )

    def __repr__(self) -> str:
        return f"<Facility(id={self.id}, name='{self.name}', category='{self.category}', verified={self.is_verified})>"


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=False, unique=True, index=True)
    assigned_area = Column(String(150), nullable=True, index=True)
    availability = Column(String(50), nullable=False, default="available")  # available, on_call, busy, offline

    # Relationships
    assigned_incidents = relationship("Incident", back_populates="volunteer")

    def __repr__(self) -> str:
        return f"<Volunteer(id={self.id}, name='{self.name}', status='{self.availability}')>"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(80), nullable=False, index=True)  # medical_emergency, water_shortage, food_shortage, sanitation_issue, lost_person, general_assistance, other
    description = Column(Text, nullable=False)
    original_message = Column(Text, nullable=True)             # Original raw user input text/transcript
    language = Column(String(20), nullable=False, default="mr-IN")
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    urgency_level = Column(String(20), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), nullable=False, default="OPEN")      # OPEN, CREATED, TRIAGED, ASSIGNED, ACKNOWLEDGED, EN_ROUTE, ON_SCENE, RESOLVED, CLOSED, CANCELLED
    location_description = Column(String(255), nullable=True)        # Location/landmark described by user
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    assigned_volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True, index=True) # Legacy mirror
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Phase 4.1 additions
    tracking_token_hash = Column(String(64), nullable=True, index=True)
    public_reference = Column(String(32), nullable=True)

    # Relationships
    user = relationship("User", back_populates="incidents")
    volunteer = relationship("Volunteer", back_populates="assigned_incidents")
    assignments = relationship("IncidentAssignment", back_populates="incident", cascade="all, delete-orphan")
    status_history = relationship("IncidentStatusHistory", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, category='{self.category}', urgency='{self.urgency_level}', status='{self.status}')>"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    refresh_token_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, nullable=False, default=False, index=True)
    replaced_by_session_id = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    legacy_volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True, unique=True)
    skills = Column(Text, nullable=True)                          # JSON array string
    sector = Column(String(150), nullable=True, index=True)       # e.g., 'Wakhari Halt Camp'
    availability = Column(String(30), nullable=False, default="offline", index=True)  # available, on_call, busy, offline
    approval_status = Column(String(30), nullable=False, default="PENDING", index=True)  # PENDING, APPROVED, SUSPENDED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=True)

    # Relationships
    user = relationship("User", back_populates="volunteer_profile")
    legacy_volunteer = relationship("Volunteer")
    assignments = relationship("IncidentAssignment", back_populates="volunteer_profile")

    def __repr__(self) -> str:
        return f"<VolunteerProfile(id={self.id}, user_id={self.user_id}, status='{self.approval_status}')>"


class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False, index=True)
    volunteer_profile_id = Column(Integer, ForeignKey("volunteer_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING", index=True)  # PENDING, ACCEPTED, REJECTED, COMPLETED, CANCELLED, REASSIGNED
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="assignments")
    volunteer_profile = relationship("VolunteerProfile", back_populates="assignments")
    assigner = relationship("User")

    def __repr__(self) -> str:
        return f"<IncidentAssignment(id={self.id}, incident_id={self.incident_id}, volunteer_profile_id={self.volunteer_profile_id}, status='{self.status}')>"


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="RESTRICT"), nullable=False, index=True)
    previous_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    reason = Column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="status_history")
    changer = relationship("User")

    def __repr__(self) -> str:
        return f"<IncidentStatusHistory(id={self.id}, incident_id={self.incident_id}, {self.previous_status}->{self.new_status})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=False)

    # Relationships
    actor = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', target='{self.target_type}:{self.target_id}')>"
