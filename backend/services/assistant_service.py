"""Assistant Intelligence Pipeline Orchestrator (Phase 3.2 Refactored).

Flow:
User text -> Intent recognition -> Confidence evaluation -> Facility retrieval or incident handling -> Response generation.

Phase 3.2 Quality, Safety & Modular Context-Aware Enforcements:
- Decoupled context-aware response composition via `response_service.py`.
- Differentiates specific nuances within each intent (e.g. routine first-aid vs collapse; water shortage vs finding tap).
- Truthful facility explanations: synthetic demo facilities are never presented as real or live-operational.
- Distance calculations occur only when valid user coordinates are present.
- Staged missing-person workflow:
    Stage 1: Recognition & empathetic response.
    Stage 2: Explicit consent inquiry (NO ticket created without consent).
    Stage 3: Minimum details intake (first name/identifier, approximate age, last seen).
    Stage 4: Incident creation with clear non-guarantee safety disclaimer.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models import Facility, Incident
from backend.services.facility_service import facility_service, sanitize_facility_for_display
from backend.services.incident_service import incident_service
from backend.services.intent_service import (
    INTENT_EMERGENCY,
    INTENT_FOOD,
    INTENT_GENERAL_INFO,
    INTENT_GREETING,
    INTENT_HELPLINE_INFO,
    INTENT_LOST_PERSON,
    INTENT_MEDICAL,
    INTENT_SANITATION,
    INTENT_SHELTER,
    INTENT_UNKNOWN,
    INTENT_WATER,
    intent_service,
)
from backend.services.response_service import build_response_for_intent
from backend.services.speech_normalization_service import speech_normalization_service


class AssistantService:
    def process_chat(
        self,
        db: Session,
        message: str,
        language: str = "mr-IN",
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        location_name: Optional[str] = None,
        user_id: Optional[int] = None,
        missing_person_consent: Optional[bool] = None,
        missing_person_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main end-to-end intelligence pipeline with Phase 3.2 modular response composition."""
        lang = (language or "mr-IN").lower()
        has_user_location = user_lat is not None and user_lon is not None

        # Step 1: Intent Recognition (or preserve intent during missing person workflow)
        if missing_person_consent is not None:
            intent = INTENT_LOST_PERSON
            confidence = 1.0
            classification_is_emergency = False
            clarification_prompt = None
        else:
            classification = intent_service.classify_intent(message, language_hint=language)
            intent = classification.intent
            confidence = classification.confidence
            classification_is_emergency = classification.is_emergency
            clarification_prompt = classification.clarification_prompt

        retrieved_facilities: List[Dict[str, Any]] = []
        incident_info: Optional[Dict[str, Any]] = None
        clarification_required = False
        awaiting_missing_person_consent = False
        awaiting_missing_person_details = False

        # Step 2: Handle domain actions (retrieval / incident creation) based on intent

        # Branch: UNKNOWN or Low Confidence
        if intent == INTENT_UNKNOWN or confidence < 0.45:
            clarification_required = True

        # Branch: Facility Queries (WATER, FOOD, SANITATION, SHELTER)
        elif intent in [INTENT_WATER, INTENT_FOOD, INTENT_SANITATION, INTENT_SHELTER]:
            cat_map = {
                INTENT_WATER: "drinking_water",
                INTENT_FOOD: "food",
                INTENT_SANITATION: "sanitation",
                INTENT_SHELTER: "resting_area"
            }
            target_cat = cat_map[intent]
            fac_results = facility_service.search_facilities(
                db=db,
                category=target_cat,
                location=location_name,
                only_verified=False,
                operational_only=True,
                user_lat=user_lat,
                user_lon=user_lon,
                limit=5
            )

            for fac, dist in fac_results:
                clean_dict = sanitize_facility_for_display(fac, language=language)
                clean_dict["distance_km"] = dist if has_user_location else None
                retrieved_facilities.append(clean_dict)

            # Check if this is a sanitation hygiene complaint/issue report
            if intent == INTENT_SANITATION and any(w in message.lower() for w in ["अस्वच्छ", "घाण", "दुर्गंधी", "गंदा", "बदबू", "dirty", "smell", "unclean", "overflow"]):
                incident = incident_service.create_incident(
                    db=db,
                    category="sanitation_issue",
                    description=f"स्वच्छतागृह तक्रार: {message}",
                    original_message=message,
                    language=language,
                    urgency_level="MEDIUM",
                    location_description=location_name,
                    latitude=user_lat,
                    longitude=user_lon,
                    user_id=user_id
                )
                incident_info = self._format_incident(incident, lang)

        # Branch: MEDICAL
        elif intent == INTENT_MEDICAL:
            fac_results = facility_service.search_facilities(
                db=db,
                category="medical",
                location=location_name,
                operational_only=True,
                user_lat=user_lat,
                user_lon=user_lon,
                limit=5
            )
            for fac, dist in fac_results:
                clean_dict = sanitize_facility_for_display(fac, language=language)
                clean_dict["distance_km"] = dist if has_user_location else None
                retrieved_facilities.append(clean_dict)

            # Check for critical medical emergency
            is_urgent_medical = (
                classification_is_emergency
                or any(w in message.lower() for w in ["तातडीने", "तातडीची", "urgent", "emergency", "अपघात", "accident", "वाचवा", "बेशुद्ध", "हार्ट", "रक्तस्त्राव", "collapsed"])
            )

            if is_urgent_medical:
                incident = incident_service.create_incident(
                    db=db,
                    category="medical_emergency",
                    description=f"तातडीची वैद्यकीय मदत विनंती: {message}",
                    original_message=message,
                    language=language,
                    urgency_level="CRITICAL" if any(w in message for w in ["बेशुद्ध", "हार्ट", "रक्तस्त्राव", "collapsed"]) else "HIGH",
                    location_description=location_name,
                    latitude=user_lat,
                    longitude=user_lon,
                    user_id=user_id
                )
                incident_info = self._format_incident(incident, lang)

        # Branch: LOST_PERSON (Staged Workflow with Consent & Privacy Guards)
        elif intent == INTENT_LOST_PERSON:
            if missing_person_consent is None:
                # Stage 1 & 2: Await explicit consent
                awaiting_missing_person_consent = True
                if lang.startswith("mr"):
                    response_text = (
                        "आम्हाला समजते की ही अत्यंत चिंतेची परिस्थिती आहे. आम्ही हरवलेल्या व्यक्तीचा शोध घेण्यासाठी मदत करू शकतो. "
                        "आपण हरवलेल्या व्यक्तीबाबत मदत नोंदणी (मिसिंग पर्सन असिस्टन्स रिक्वेस्ट) करू इच्छिता का? "
                        "(कृपया 'होय' किंवा 'नाही' निवडा. आपली वैयक्तिक माहिती सुरक्षित ठेवली जाईल.)"
                    )
                elif lang.startswith("hi"):
                    response_text = (
                        "हम समझ सकते हैं कि यह चिंता का विषय है। हम लापता व्यक्ति की खोज में सहायता कर सकते हैं। "
                        "क्या आप लापता व्यक्ति सहायता अनुरोध दर्ज करना चाहते हैं? "
                        "(कृपया 'हाँ' या 'नहीं' चुनें। आपकी जानकारी सुरक्षित रखी जाएगी।)"
                    )
                else:
                    response_text = (
                        "We understand this is a very stressful situation, and we can help coordinate search efforts. "
                        "Would you like to register a missing-person assistance request with the coordination team? "
                        "(Please confirm with 'Yes' or 'No'. Personal information will be kept strictly private.)"
                    )
                return {
                    "intent": intent,
                    "confidence": round(confidence, 2),
                    "response_text": response_text,
                    "speech_text": speech_normalization_service.normalize_for_speech(response_text, language=lang),
                    "facilities": [],
                    "incident": None,
                    "clarification_required": False,
                    "awaiting_missing_person_consent": True,
                    "awaiting_missing_person_details": False
                }

            elif missing_person_consent is False:
                # User declined
                if lang.startswith("mr"):
                    response_text = "समजले. कोणतीही तक्रार नोंदवली नाही. आपल्याला पिण्याचे पाणी, अन्नछत्र किंवा इतर मार्गदर्शनाची मदत हवी असल्यास विचारू शकता."
                elif lang.startswith("hi"):
                    response_text = "ठीक है, कोई अनुरोध दर्ज नहीं किया गया है। यदि आपको पानी, भोजन या मार्ग की जानकारी चाहिए, तो कृपया बताएं।"
                else:
                    response_text = "Understood. No missing-person request has been recorded. Let us know if you need any other pilgrimage guidance."
                return {
                    "intent": intent,
                    "confidence": round(confidence, 2),
                    "response_text": response_text,
                    "speech_text": speech_normalization_service.normalize_for_speech(response_text, language=lang),
                    "facilities": [],
                    "incident": None,
                    "clarification_required": False,
                    "awaiting_missing_person_consent": False,
                    "awaiting_missing_person_details": False
                }

            else:
                # Consented: Stage 3 & 4
                details = missing_person_details or {}
                name = details.get("name") or details.get("identifier")
                age = details.get("age") or details.get("age_range")
                last_seen = details.get("last_seen") or location_name

                if not name and len(message.strip().split()) >= 4 and any(w in message for w in ["माझे", "माझी", "वडील", "मुलगा", "father", "mother"]):
                    name = "व्यक्ति (वर्णनानुसार)"

                if not name and not details:
                    awaiting_missing_person_details = True
                    if lang.startswith("mr"):
                        response_text = (
                            "कृपया केवळ आवश्यक तपशील द्या: "
                            "१. हरवलेल्या व्यक्तीचे नाव किंवा टोपणनाव, "
                            "२. अंदाजे वय, आणि "
                            "३. शेवटचे कोठे पाहिले होते? "
                            "(आम्ही आधार किंवा गोपनीय वैयक्तिक माहिती विचारत नाही.)"
                        )
                    elif lang.startswith("hi"):
                        response_text = (
                            "कृपया केवल न्यूनतम आवश्यक जानकारी प्रदान करें: "
                            "1. व्यक्ति का नाम, "
                            "2. अनुमानित आयु, और "
                            "3. अंतिम बार कहाँ देखा गया था? "
                            "(हम आधार या गोपनीय व्यक्तिगत जानकारी नहीं मांगते।)"
                        )
                    else:
                        response_text = (
                            "Please provide only the necessary coordination details: "
                            "1. Missing person's first name or identifier, "
                            "2. Approximate age range, and "
                            "3. Last known location. "
                            "(We do not collect Aadhaar or sensitive financial details.)"
                        )
                    return {
                        "intent": intent,
                        "confidence": round(confidence, 2),
                        "response_text": response_text,
                        "speech_text": speech_normalization_service.normalize_for_speech(response_text, language=lang),
                        "facilities": [],
                        "incident": None,
                        "clarification_required": False,
                        "awaiting_missing_person_consent": False,
                        "awaiting_missing_person_details": True
                    }

                # Stage 4: Create incident
                constructed_desc = f"हरवलेली व्यक्ती शोध मोहीम: नाव: {name or 'नमुद नाही'}, वय: {age or 'अंदाजे'}, ठिकाण: {last_seen or 'अज्ञात'} | मूळ संदेश: {message}"
                incident = incident_service.create_incident(
                    db=db,
                    category="lost_person",
                    description=constructed_desc,
                    original_message=message,
                    language=language,
                    urgency_level="HIGH",
                    location_description=last_seen,
                    latitude=user_lat,
                    longitude=user_lon,
                    user_id=user_id
                )
                incident_info = self._format_incident(incident, lang)

                if lang.startswith("mr"):
                    response_text = (
                        f"हरवलेल्या व्यक्तीबाबत आपली विनंती (तिकीट #{incident.id}) सुरक्षितपणे नोंदवली आहे. "
                        "आपली नोंदणी प्राप्त झाली आहे. याचा अर्थ स्वयंसेवक त्वरित नियुक्त झाला आहे किंवा आपत्कालीन सेवांशी संपर्क झाला आहे असा नाही."
                    )
                elif lang.startswith("hi"):
                    response_text = (
                        f"लापता व्यक्ति की सहायता टिकट (#{incident.id}) सुरक्षित रूप से दर्ज कर ली गई है। "
                        "आपका अनुरोध दर्ज कर लिया गया है। इसका यह अर्थ नहीं है कि स्वयंसेवक नियुक्त हो गया है या आपातकालीन सेवाओं से संपर्क हो चुका है।"
                    )
                else:
                    response_text = (
                        f"Your missing-person assistance request (#{incident.id}) has been recorded. "
                        "Your request has been recorded. This does not mean a volunteer has been assigned or that emergency services have been contacted."
                    )

                return {
                    "intent": intent,
                    "confidence": round(confidence, 2),
                    "response_text": response_text,
                    "speech_text": speech_normalization_service.normalize_for_speech(response_text, language=lang),
                    "facilities": [],
                    "incident": incident_info,
                    "clarification_required": False,
                    "awaiting_missing_person_consent": False,
                    "awaiting_missing_person_details": False
                }

        # Branch: EMERGENCY
        elif intent == INTENT_EMERGENCY:
            incident = incident_service.create_incident(
                db=db,
                category="other",
                description=f"आणीबाणी अलर्ट: {message}",
                original_message=message,
                language=language,
                urgency_level="CRITICAL",
                location_description=location_name,
                latitude=user_lat,
                longitude=user_lon,
                user_id=user_id
            )
            incident_info = self._format_incident(incident, lang)

        # Step 3: Compose Context-Aware Response via Modular Response Service
        response_text = build_response_for_intent(
            intent=intent,
            user_query=message,
            facilities=retrieved_facilities,
            incident=incident_info,
            language=lang,
            has_user_location=has_user_location,
            clarification_prompt=clarification_prompt
        )

        speech_text = speech_normalization_service.normalize_for_speech(response_text, language=lang)

        return {
            "intent": intent,
            "confidence": round(confidence, 2),
            "response_text": response_text,
            "speech_text": speech_text,
            "facilities": retrieved_facilities,
            "incident": incident_info,
            "clarification_required": clarification_required,
            "awaiting_missing_person_consent": awaiting_missing_person_consent,
            "awaiting_missing_person_details": awaiting_missing_person_details
        }

    def _format_incident(self, incident: Incident, lang: str) -> Dict[str, Any]:
        if lang.startswith("mr"):
            disclaimer = "आपली नोंदणी प्राप्त झाली आहे. याचा अर्थ स्वयंसेवक त्वरित नियुक्त झाला आहे किंवा आपत्कालीन सेवांशी संपर्क झाला आहे असा नाही."
        elif lang.startswith("hi"):
            disclaimer = "आपका अनुरोध दर्ज कर लिया गया है। इसका यह अर्थ नहीं है कि स्वयंसेवक नियुक्त हो गया है या आपातकालीन सेवाओं से संपर्क हो चुका है।"
        else:
            disclaimer = "Your request has been recorded. This does not mean a volunteer has been assigned or that emergency services have been contacted."

        return {
            "id": incident.id,
            "category": incident.category,
            "description": incident.description,
            "urgency_level": incident.urgency_level,
            "status": incident.status,
            "location_description": incident.location_description,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "safety_disclaimer": disclaimer
        }


assistant_service = AssistantService()
