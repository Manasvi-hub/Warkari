"""Facility Retrieval Service for Warkari Pilgrimage Assistance.

Operates over the SQLite `facilities` table.
Supports category search, keyword matching, operational/verified filtering,
and haversine distance calculation when GPS coordinates are provided.

Enforces strict verification and contact safety rules:
- Synthetic demo facilities (is_demo=True) can NEVER be marked or returned as verified.
- Contact information is only returned when a facility is not demo, verified, and has a valid verified phone.
"""

import math
from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models import Facility

CATEGORY_SYNONYMS = {
    "water": "drinking_water",
    "drinking_water": "drinking_water",
    "paani": "drinking_water",
    "medical": "medical",
    "hospital": "medical",
    "first_aid": "medical",
    "sanitation": "sanitation",
    "toilet": "sanitation",
    "washroom": "sanitation",
    "food": "food",
    "meal": "food",
    "annachhatra": "food",
    "shelter": "resting_area",
    "resting_area": "resting_area",
    "camp": "resting_area",
    "emergency": "emergency",
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def sanitize_facility_for_display(fac: Facility, language: str = "mr-IN") -> dict:
    """Applies strict data sanitization to prevent misleading verification or fake contacts,
    with Phase 3.3.5 multilingual resolution and explicit fallback tracking.

    Case A: Synthetic demo facility (is_demo=True)
      - is_verified is forced to False.
      - contact_phone is forced to None (no fake numbers).
      - display_label: "DEMO DATA"

    Case B: Genuine verified facility (is_demo=False and is_verified=True)
      - display_label: "VERIFIED"
      - contact_phone is preserved only if non-empty and non-placeholder.

    Case C: Unverified real facility (is_demo=False and is_verified=False)
      - display_label: "UNVERIFIED"
      - operational status is presented as unconfirmed.
      - contact_phone is omitted unless verified.
    """
    is_demo = bool(fac.is_demo)
    is_verified = False if is_demo else bool(fac.is_verified)

    if is_demo:
        display_status = "DEMO DATA"
        operational = "unconfirmed (demo)"
        safe_contact = None
    elif is_verified:
        display_status = "VERIFIED"
        operational = fac.operational_status or "operational"
        # Validate contact: must not be placeholder or dummy
        raw_phone = (fac.contact_phone or "").strip()
        if raw_phone and not any(p in raw_phone for p in ["00000", "12345", "test", "demo"]):
            safe_contact = raw_phone
        else:
            safe_contact = None
    else:
        display_status = "UNVERIFIED"
        operational = "unverified"
        safe_contact = None

    # Language resolution (Phase 3.3.5)
    lang_code = (language or "mr-IN").lower()
    req_lang = "mr"
    if lang_code.startswith("en"):
        req_lang = "en"
    elif lang_code.startswith("hi"):
        req_lang = "hi"

    name_val = fac.name
    loc_val = fac.location
    desc_val = fac.description

    name_fallback = False
    loc_fallback = False
    desc_fallback = False

    if req_lang == "en":
        if getattr(fac, "name_en", None):
            name_val = fac.name_en
        else:
            name_fallback = True

        if getattr(fac, "location_en", None):
            loc_val = fac.location_en
        else:
            loc_fallback = True

        if getattr(fac, "description_en", None):
            desc_val = fac.description_en
        else:
            desc_fallback = True

    elif req_lang == "hi":
        if getattr(fac, "name_hi", None):
            name_val = fac.name_hi
        else:
            name_fallback = True

        if getattr(fac, "location_hi", None):
            loc_val = fac.location_hi
        else:
            loc_fallback = True

        if getattr(fac, "description_hi", None):
            desc_val = fac.description_hi
        else:
            desc_fallback = True

    overall_fallback = name_fallback or loc_fallback or desc_fallback
    resolved_lang = "mr" if (req_lang != "mr" and overall_fallback and not getattr(fac, f"name_{req_lang}", None)) else req_lang

    return {
        "id": fac.id,
        "name": name_val,
        "category": fac.category,
        "description": desc_val,
        "location": loc_val,
        "latitude": fac.latitude,
        "longitude": fac.longitude,
        "operational_status": operational,
        "is_verified": is_verified,
        "is_demo": is_demo,
        "display_status": display_status,
        "source": fac.source,
        "contact_phone": safe_contact,
        "last_verified_at": fac.last_verified_at.isoformat() if (fac.last_verified_at and not is_demo) else None,
        # Multilingual & Fallback Metadata
        "requested_language": req_lang,
        "resolved_language": resolved_lang,
        "language_fallback": overall_fallback,
        "name_fallback": name_fallback,
        "location_fallback": loc_fallback,
        "description_fallback": desc_fallback,
        "name_en": getattr(fac, "name_en", None),
        "name_hi": getattr(fac, "name_hi", None),
        "location_en": getattr(fac, "location_en", None),
        "location_hi": getattr(fac, "location_hi", None),
        "description_en": getattr(fac, "description_en", None),
        "description_hi": getattr(fac, "description_hi", None),
    }


class FacilityService:
    def normalize_category(self, cat: Optional[str]) -> Optional[str]:
        if not cat:
            return None
        clean = cat.strip().lower().replace(" ", "_")
        return CATEGORY_SYNONYMS.get(clean, clean)

    def search_facilities(
        self,
        db: Session,
        category: Optional[str] = None,
        query: Optional[str] = None,
        location: Optional[str] = None,
        only_verified: bool = False,
        operational_only: bool = True,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        limit: int = 10
    ) -> List[Tuple[Facility, Optional[float]]]:
        """Retrieves matching facilities with distance sorting if user GPS coordinates provided."""
        stmt = db.query(Facility)

        norm_cat = self.normalize_category(category)
        if norm_cat:
            stmt = stmt.filter(Facility.category == norm_cat)

        if only_verified:
            # Synthetic demo data cannot be returned when verified only is requested
            stmt = stmt.filter(Facility.is_verified == True, Facility.is_demo == False)

        if operational_only:
            stmt = stmt.filter(Facility.operational_status == "operational")

        if location:
            loc_clean = f"%{location.strip()}%"
            stmt = stmt.filter(
                or_(
                    Facility.location.ilike(loc_clean),
                    Facility.name.ilike(loc_clean)
                )
            )

        if query:
            q_clean = f"%{query.strip()}%"
            stmt = stmt.filter(
                or_(
                    Facility.name.ilike(q_clean),
                    Facility.description.ilike(q_clean),
                    Facility.location.ilike(q_clean)
                )
            )

        records = stmt.all()

        results_with_dist: List[Tuple[Facility, Optional[float]]] = []
        for fac in records:
            dist = None
            if user_lat is not None and user_lon is not None and fac.latitude is not None and fac.longitude is not None:
                try:
                    dist = round(haversine_distance(user_lat, user_lon, fac.latitude, fac.longitude), 2)
                except Exception:
                    dist = None
            results_with_dist.append((fac, dist))

        # Sort: first by distance if available, then genuine verified descending, then demo/unverified
        if user_lat is not None and user_lon is not None:
            results_with_dist.sort(key=lambda item: (item[1] is None, item[1] if item[1] is not None else 999999))
        else:
            results_with_dist.sort(key=lambda item: (not (item[0].is_verified and not item[0].is_demo), item[0].id))

        return results_with_dist[:limit]

    def get_facility_by_id(self, db: Session, facility_id: int) -> Optional[Facility]:
        return db.query(Facility).filter(Facility.id == facility_id).first()


facility_service = FacilityService()
