"""Intent Recognition Engine for Warkari Pilgrimage Platform.

Classifies user requests across 10 canonical intent categories:
- GREETING: Polite greetings and general introductions
- WATER: Drinking water requests, tanker locations
- MEDICAL: First aid, dispensary, ambulance, doctors
- FOOD: Annachhatra, food packets, prasad, meals
- SANITATION: Public toilets, washrooms, mobile toilets
- SHELTER: Resting tents, dharamshala, night stay, shade
- LOST_PERSON: Missing person, child or elder separated
- EMERGENCY: Critical distress, accident, stampede, heart issue
- GENERAL_INFO: Palkhi schedule, darshan queue, routes
- UNKNOWN: Ambiguous, out-of-domain, or unrecognizable inputs

Languages supported:
- Marathi (Devanagari: mr-IN)
- Hindi (Devanagari: hi-IN)
- English (en-IN)
- Common Marathi transliterations written in Latin characters (Hinglish/Marathish)
"""

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel


class IntentResult(BaseModel):
    intent: str
    confidence: float
    matched_keywords: List[str] = []
    language_hint: Optional[str] = None
    is_emergency: bool = False
    clarification_prompt: Optional[str] = None


# Canonical Intents
INTENT_GREETING = "GREETING"
INTENT_WATER = "WATER"
INTENT_MEDICAL = "MEDICAL"
INTENT_FOOD = "FOOD"
INTENT_SANITATION = "SANITATION"
INTENT_SHELTER = "SHELTER"
INTENT_LOST_PERSON = "LOST_PERSON"
INTENT_EMERGENCY = "EMERGENCY"
INTENT_HELPLINE_INFO = "HELPLINE_INFO"
INTENT_GENERAL_INFO = "GENERAL_INFO"
INTENT_UNKNOWN = "UNKNOWN"

ALL_INTENTS = [
    INTENT_GREETING,
    INTENT_WATER,
    INTENT_MEDICAL,
    INTENT_FOOD,
    INTENT_SANITATION,
    INTENT_SHELTER,
    INTENT_LOST_PERSON,
    INTENT_EMERGENCY,
    INTENT_HELPLINE_INFO,
    INTENT_GENERAL_INFO,
    INTENT_UNKNOWN,
]

# Keyword dictionary with category weightings
INTENT_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    INTENT_HELPLINE_INFO: {
        "mr": [
            "कोणत्या नंबरवर फोन", "कोणत्या नंबरवर", "आपत्कालीन नंबर", "आपत्कालीन फोन", "रुग्णवाहिका नंबर",
            "१०८ नंबर", "108 नंबर", "हेल्पलाईन", "मदत क्रमांक", "पोलीस नंबर", "फोन नंबर काय आहे",
            "आपत्कालीन परिस्थितीत काय करावे", "आपत्कालीन फोन नंबर"
        ],
        "hi": [
            "किस नंबर पर कॉल", "आपातकालीन नंबर", "एम्बुलेंस नंबर", "१०८ नंबर", "108 नंबर",
            "हेल्पलाइन", "इमरजेंसी नंबर", "सहायता नंबर", "फोन नंबर क्या है", "किस नंबर पर संपर्क करें"
        ],
        "en": [
            "emergency ambulance number", "emergency number", "ambulance number", "call in a medical emergency",
            "what is 108", "helpline number", "what number should i call", "who should i call in emergency",
            "emergency helpline", "helpline", "what is the emergency number", "emergency contact number"
        ],
        "translit": [
            "emergency number", "ambulance number", "helpline", "phone number", "kontya number"
        ]
    },
    INTENT_GREETING: {
        "mr": [
            "नमस्कार", "राम कृष्ण हरी", "जय हरी", "जय हरी विठ्ठल", "हरि बोल", "प्रणाम", "सुप्रभात"
        ],
        "hi": [
            "नमस्ते", "प्रणाम", "जय श्री कृष्णा", "शुभ प्रभात", "जय विट्ठल"
        ],
        "en": [
            "hello", "hi", "hey", "greetings", "good morning", "good evening", "can you help me"
        ],
        "translit": [
            "namaskar", "ram krishna hari", "jai hari", "namaste", "pranam"
        ]
    },
    INTENT_WATER: {
        "mr": [
            "पाणी", "पिण्याचे पाणी", "पिण्याचं पाणी", "पाण्याचा टँकर", "जल", "तहान",
            "पाणी कुठे", "पाणी मिळेल का", "जलसेवा", "पिण्यायोग्य पाणी", "पाणी संपले"
        ],
        "hi": [
            "पानी", "पीने का पानी", "जल", "पानी कहाँ", "पानी मिलेगा", "प्यासा", "पानी का टैंकर"
        ],
        "en": [
            "water", "drinking water", "water tanker", "thirsty", "tap water", "water bottle"
        ],
        "translit": [
            "paani", "pani", "pinya che pani", "pinyache pani", "peene ka pani", "pani kuthe", "pani milel"
        ]
    },
    INTENT_MEDICAL: {
        "mr": [
            "वैद्यकीय", "औषध", "दवाखाना", "डॉक्टर", "प्रथमोपचार", "तपासणी", "आजारी",
            "रुग्णवाहिका", "रुग्णालय", "चक्कर", "उलटी", "जुलाब", "पाय दुखतात", "जखम", "गोळ्या"
        ],
        "hi": [
            "चिकित्सा", "दवाई", "दवा", "डॉक्टर", "अस्पताल", "प्राथमिक उपचार", "बीमार",
            "एम्बुलेंस", "इलाज", "चोट", "दर्द"
        ],
        "en": [
            "medical", "medicine", "doctor", "hospital", "clinic", "first aid", "sick",
            "ambulance", "injury", "wound", "treatment", "pain", "fever"
        ],
        "translit": [
            "vaidyakiya", "aushadh", "davakhana", "doctor", "prathamopchar", "aajari",
            "rugnavahika", "dava", "madat havi", "medical help"
        ]
    },
    INTENT_FOOD: {
        "mr": [
            "अन्नछत्र", "जेवण", "भोजन", "अन्न", "प्रसाद", "नाश्ता", "खाण्यापिण्याची", "भूक", "जेवण कुठे"
        ],
        "hi": [
            "भोजन", "खाना", "अन्नक्षेत्र", "प्रसाद", "नाश्ता", "भूख", "खाने की व्यवस्था"
        ],
        "en": [
            "food", "meal", "lunch", "dinner", "breakfast", "prasad", "canteen", "hungry", "eat"
        ],
        "translit": [
            "annachhatra", "jevan", "bhojan", "khana", "jevan kuthe", "prasad", "nashta", "bhuk"
        ]
    },
    INTENT_SANITATION: {
        "mr": [
            "स्वच्छतागृह", "शौचालय", "टॉयलेट", "संडास", "मूत्रालय", "बाथरूम", "शौच"
        ],
        "hi": [
            "शौचालय", "टॉयलेट", "सुलभ शौचालय", "मूत्रालय", "गुसलखाना"
        ],
        "en": [
            "toilet", "washroom", "restroom", "latrine", "bathroom", "sanitation", "urinal"
        ],
        "translit": [
            "swachhatagruh", "shauchalay", "toilet", "washroom", "mutralay", "sandas"
        ]
    },
    INTENT_SHELTER: {
        "mr": [
            "विश्रांती", "विश्राम", "तंबू", "धर्मशाळा", "मुक्काम", "थांबण्याची जागा", "विसावा",
            "झोपण्याची जागा", "आश्रय", "रात्र मुक्काम", "विसावा कुठे"
        ],
        "hi": [
            "विश्राम", "रुकने की जगह", "धर्मशाला", "तंबू", "आश्रय", "रैन बसेरा", "सोने की जगह"
        ],
        "en": [
            "shelter", "rest", "resting area", "stay", "tent", "dharamshala", "night stay", "camp", "sleep"
        ],
        "translit": [
            "vishranti", "mukkam", "tambu", "dharamshala", "visawa", "rukne ki jagah", "stay"
        ]
    },
    INTENT_LOST_PERSON: {
        "mr": [
            "हरवली", "हरवला", "हरवले", "सापडत नाही", "दिसत नाही", "माझे वडील", "माझी आई",
            "माझा मुलगा", "माझी मुलगी", "व्यक्ती हरवली", "माणूस हरवला", "गहाळ"
        ],
        "hi": [
            "खो गया", "खो गई", "लापता", "मिल नहीं रहे", "गुमशुदा", "मेरे पिता", "मेरी माता", "बच्चा खो गया"
        ],
        "en": [
            "lost person", "missing", "lost someone", "cannot find", "lost my father", "lost my mother",
            "lost child", "separated from group", "missing person"
        ],
        "translit": [
            "haravle", "haravla", "haravali", "sapadat nahi", "kho gaya", "kho gayi", "lapata", "missing", "lost"
        ]
    },
    INTENT_EMERGENCY: {
        "mr": [
            "तातडीची मदत", "आणीबाणी", "गंभीर", "अपघात", "हार्ट अटॅक", "जीव धोक्यात",
            "बेशुद्ध", "रक्तस्त्राव", "दगडी मारामारी", "चेंगराचेंगरी", "मदत करा वाचवा", "वाचवा"
        ],
        "hi": [
            "आपातकाल", "दुर्घटना", "हादसा", "बेहोश", "खून बह रहा", "भगदड़", "जान का खतरा", "बचाओ"
        ],
        "en": [
            "emergency", "critical", "urgent help", "accident", "unconscious", "heart attack",
            "stampede", "bleeding", "save us", "danger"
        ],
        "translit": [
            "emergency", "tatadichi madat", "aanibani", "bachao", "vachva", "apghat", "critical", "urgent"
        ]
    },
    INTENT_GENERAL_INFO: {
        "mr": [
            "पालखी मार्ग", "पालखीचा मार्ग", "पालखी", "मार्ग", "वारी", "पंढरपूर", "दर्शन", "वेळापत्रक", "मुक्काम स्थळ",
            "माहिती", "रस्ता", "कधी पोहोचणार", "अंतर", "मंदिराची वेळ"
        ],
        "hi": [
            "पालकी मार्ग", "पंढरपुर", "दर्शन", "समय सारणी", "रास्ता", "दूरी", "मंदिर का समय"
        ],
        "en": [
            "palkhi route", "pandharpur", "wari schedule", "darshan time", "distance",
            "direction", "temple timing", "schedule", "information", "route"
        ],
        "translit": [
            "palkhi marg", "darshan", "velapatrak", "pandharpur", "rasta", "wari", "schedule", "route"
        ]
    }
}


class IntentService:
    def __init__(self):
        pass

    def classify_intent(self, text: str, language_hint: Optional[str] = "mr-IN") -> IntentResult:
        """Classifies text into one of the canonical intents with confidence scoring."""
        clean_text = (text or "").strip().lower()
        if not clean_text:
            return IntentResult(
                intent=INTENT_UNKNOWN,
                confidence=0.0,
                matched_keywords=[],
                language_hint=language_hint,
                clarification_prompt=self._get_clarification_prompt(language_hint)
            )

        # 0. Pre-check for Informational Helpline Inquiries (Emergency Number / 108 questions)
        # Checked before active emergency so "what is the emergency number?" does NOT register an active distress ticket.
        helpline_matched = self._match_category(clean_text, INTENT_HELPLINE_INFO)
        if helpline_matched:
            return IntentResult(
                intent=INTENT_HELPLINE_INFO,
                confidence=min(1.0, 0.75 + len(helpline_matched) * 0.15),
                matched_keywords=helpline_matched,
                language_hint=language_hint,
                is_emergency=False,
                clarification_prompt=None
            )

        # 1. Pre-check for life-safety emergency keywords
        emergency_matched = self._match_category(clean_text, INTENT_EMERGENCY)
        if emergency_matched:
            return IntentResult(
                intent=INTENT_EMERGENCY,
                confidence=min(1.0, 0.65 + len(emergency_matched) * 0.15),
                matched_keywords=emergency_matched,
                language_hint=language_hint,
                is_emergency=True,
                clarification_prompt=None
            )

        # 2. Pre-check for missing person
        lost_matched = self._match_category(clean_text, INTENT_LOST_PERSON)
        if lost_matched:
            return IntentResult(
                intent=INTENT_LOST_PERSON,
                confidence=min(1.0, 0.70 + len(lost_matched) * 0.15),
                matched_keywords=lost_matched,
                language_hint=language_hint,
                is_emergency=False,
                clarification_prompt=None
            )

        # 3. Check for specific assistance requests (WATER, MEDICAL, FOOD, SANITATION, SHELTER, GENERAL_INFO)
        # We check specific intents before GREETING so "Hello, where is water?" prioritizes WATER
        domain_scores: Dict[str, Tuple[float, List[str]]] = {}
        for intent_cat in [INTENT_WATER, INTENT_MEDICAL, INTENT_FOOD, INTENT_SANITATION, INTENT_SHELTER, INTENT_GENERAL_INFO]:
            matched = self._match_category(clean_text, intent_cat)
            if matched:
                score = min(0.95, 0.50 + len(matched) * 0.20)
                domain_scores[intent_cat] = (score, matched)

        if domain_scores:
            top_intent = max(domain_scores.keys(), key=lambda k: domain_scores[k][0])
            top_score, matched_words = domain_scores[top_intent]
            if top_score >= 0.45:
                return IntentResult(
                    intent=top_intent,
                    confidence=top_score,
                    matched_keywords=matched_words,
                    language_hint=language_hint,
                    is_emergency=False,
                    clarification_prompt=None
                )

        # 4. Check for Greeting intent if no domain-specific intent was strongly matched
        greeting_matched = self._match_category(clean_text, INTENT_GREETING)
        if greeting_matched:
            return IntentResult(
                intent=INTENT_GREETING,
                confidence=0.85,
                matched_keywords=greeting_matched,
                language_hint=language_hint,
                is_emergency=False,
                clarification_prompt=None
            )

        # Fallback to UNKNOWN
        return IntentResult(
            intent=INTENT_UNKNOWN,
            confidence=0.20,
            matched_keywords=[],
            language_hint=language_hint,
            clarification_prompt=self._get_clarification_prompt(language_hint)
        )

    def _match_category(self, text: str, category: str) -> List[str]:
        """Finds matched keywords for a category across all sub-dictionaries."""
        matched = []
        cat_dict = INTENT_PATTERNS.get(category, {})
        for lang_key, keywords in cat_dict.items():
            for kw in keywords:
                if re.search(r'(?i)' + re.escape(kw), text):
                    matched.append(kw)
        return list(set(matched))

    def _get_clarification_prompt(self, language_hint: Optional[str]) -> str:
        lang = (language_hint or "mr-IN").lower()
        if lang.startswith("mr"):
            return "माफ करा, मला आपला प्रश्न स्पष्ट समजला नाही. आपल्याला पाणी, दवाखाना, अन्नछत्र, शौचालय, मुक्काम की हरवलेल्या व्यक्तीबाबत मदत हवी आहे का?"
        elif lang.startswith("hi"):
            return "क्षमा करें, मुझे आपका प्रश्न पूरी तरह समझ नहीं आया। क्या आपको पानी, दवाखाना, भोजन, शौचालय, विश्राम स्थल या लापता व्यक्ति के संबंध में सहायता चाहिए?"
        else:
            return "Pardon me, I could not determine your exact request. Do you need assistance with drinking water, medical aid, food, restrooms, shelter, or a missing person?"


intent_service = IntentService()
