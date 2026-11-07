"""Pronunciation and Speech Normalization Dictionary for Warkari Pilgrimage Platform.

Maintains:
- Centralized Warkari-specific pronunciation lexicon for key pilgrimage route stops,
  religious landmarks, local expressions, and Wari-related terminology.
- Display text preservation (official pilgrimage names in English Latin) vs.
  authentic native Devanagari speech representation for Gnani Timbre neural TTS.
- Safe phrase-level matching (longest phrases matched first, complete words only,
  Devanagari immunity to prevent double-substitutions).
"""

from typing import Dict, List, Optional, Tuple
import re

# Centralized Lexicon mapping English display terms to native Devanagari representations.
# Organized by category:
# 1. Multi-word religious & cultural landmarks / phrases
# 2. Saints & Deities
# 3. Wari & Pilgrimage pilgrimage terminology
# 4. Palkhi route halts & holy locations
WARKARI_PRONUNCIATION_LEXICON: List[Tuple[str, str]] = [
    # --- 1. Multi-word phrases & landmarks (Must match before individual words) ---
    ("Sant Dnyaneshwar Maharaj Palkhi Sohala", "संत ज्ञानेश्वर महाराज पालखी सोहळा"),
    ("Sant Tukaram Maharaj Palkhi Sohala", "संत तुकाराम महाराज पालखी सोहळा"),
    ("Sant Dnyaneshwar Maharaj", "संत ज्ञानेश्वर महाराज"),
    ("Sant Tukaram Maharaj", "संत तुकाराम महाराज"),
    ("Dnyaneshwar Maharaj", "ज्ञानेश्वर महाराज"),
    ("Tukaram Maharaj", "तुकाराम महाराज"),
    ("Vitthal Rukmini Mandir", "विठ्ठल रुक्मिणी मंदिर"),
    ("Vitthal-Rukmini Mandir", "विठ्ठल रुक्मिणी मंदिर"),
    ("Vitthal Rukmini Temple", "विठ्ठल रुक्मिणी मंदिर"),
    ("Vitthal-Rukmini Temple", "विठ्ठल रुक्मिणी मंदिर"),
    ("Vitthal Mandir", "विठ्ठल मंदिर"),
    ("Vitthal Temple", "विठ्ठल मंदिर"),
    ("Rukmini Mandir", "रुक्मिणी मंदिर"),
    ("Rukmini Temple", "रुक्मिणी मंदिर"),
    ("Chandrabhaga Ghat", "चंद्रभागा घाट"),
    ("Chandrabhaga River", "चंद्रभागा नदी"),
    ("Palkhi Sohala", "पालखी सोहळा"),
    ("Ashadhi Wari", "आषाढी वारी"),
    ("Kartiki Wari", "कार्तिकी वारी"),
    ("Padsparsh Darshan", "पदस्पर्श दर्शन"),
    ("Charansparsh", "चरणस्पर्श"),
    ("Mukh Darshan", "मुखदर्शन"),
    ("Jai Hari Vitthal", "जय हरी विठ्ठल"),
    ("Wakhari Halt", "वाखरी मुक्काम"),
    ("Mukam Tal", "मुक्काम तळ"),
    ("Mukam", "मुक्काम"),

    # --- 2. Deities & Saints (Single names) ---
    ("Vitthal", "विठ्ठल"),
    ("Vithoba", "विठोबा"),
    ("Pandurang", "पांडुरंग"),
    ("Rukmini", "रुक्मिणी"),
    ("Rakhumai", "रखुमाई"),
    ("Dnyaneshwar", "ज्ञानेश्वर"),
    ("Tukaram", "तुकाराम"),
    ("Namdev", "नामदेव"),
    ("Eknath", "एकनाथ"),
    ("Chokhamela", "चोखामेळा"),
    ("Nivruttinath", "निवृत्तीनाथ"),
    ("Sopandev", "सोपानदेव"),
    ("Muktabai", "मुक्ताबाई"),

    # --- 3. Wari & Pilgrimage Terminology ---
    ("Warkari", "वारकरी"),
    ("Varkari", "वारकरी"),
    ("Wari", "वारी"),
    ("Vari", "वारी"),
    ("Palkhi", "पालखी"),
    ("Dindi", "दिंडी"),
    ("Abhang", "अभंग"),
    ("Bhajan", "भजन"),
    ("Kirtan", "कीर्तन"),
    ("Mahaprasad", "महाप्रसाद"),
    ("Annachhatra", "अन्नछत्र"),
    ("Darshan", "दर्शन"),
    ("Prasad", "प्रसाद"),
    ("Ghat", "घाट"),
    ("Taal", "टाळ"),
    ("Mridanga", "मृदंग"),
    ("Pakhawaj", "पखवाज"),
    ("Veena", "वीणा"),
    ("Tulsi Vrindavan", "तुळशी वृंदावन"),
    ("Pataka", "पताका"),

    # --- 4. Palkhi Route Halts & Sacred Locations (Phase 3.3.1 preservation) ---
    ("Pandharpur", "पंढरपूर"),
    ("Wakhari", "वाखरी"),
    ("Pune", "पुणे"),
    ("Saswad", "सासवड"),
    ("Jejuri", "जेजुरी"),
    ("Lonand", "लोणंद"),
    ("Phaltan", "फलटण"),
    ("Velapur", "वेळापूर"),
    ("Chandrabhaga", "चंद्रभागा"),
    ("Dehu", "देहू"),
    ("Alandi", "आळंदी"),
    ("Natepute", "नातेपुते"),
    ("Malshiras", "माळशिरस"),
    ("Mohol", "मोहोळ"),
    ("Taradgaon", "तरडगाव"),
    ("Bhadalwadi", "भाडलवाडी"),
    ("Shegaon", "शेगाव")
]


class PronunciationService:
    """Centralized Warkari-specific pronunciation service for TTS speech text."""

    def __init__(self, lexicon: Optional[List[Tuple[str, str]]] = None):
        # Sort lexicon strictly by phrase length descending (longest phrase matched first)
        raw_lexicon = lexicon or WARKARI_PRONUNCIATION_LEXICON
        self.lexicon: List[Tuple[str, str]] = sorted(
            raw_lexicon,
            key=lambda item: len(item[0]),
            reverse=True
        )

    def apply_pronunciation_to_text(self, text: str, language: str = "en-IN") -> str:
        """Applies pronunciation adjustments to a sentence for natural TTS synthesis.

        Requirements:
        - When language is 'en-IN', substitute English Marathi-origin terms and place names
          with authentic native Devanagari spellings (which Gnani Timbre neural model authentically synthesizes).
        - Match longest phrases before shorter phrases (e.g. 'Vitthal Rukmini Mandir' before 'Vitthal').
        - Match complete words or phrases only via word boundaries (\b).
        - Avoid accidental substitutions inside ordinary English words.
        - Marathi ('mr-IN') and Hindi ('hi-IN') speech texts are left unaltered as they already use Devanagari.
        """
        if not text:
            return ""

        lang = (language or "en-IN").lower()
        if not lang.startswith("en"):
            # Marathi and Hindi texts already use native Devanagari script
            return text

        processed = text

        for eng_phrase, dev_target in self.lexicon:
            # Use regex with word boundaries (\b) and case-insensitivity
            # Note: Avoid matching if already transformed to Devanagari
            pattern = re.compile(rf"\b{re.escape(eng_phrase)}\b", re.IGNORECASE)
            processed = pattern.sub(dev_target, processed)

        return processed

    def get_speech_name(self, term: str, language: str = "en-IN") -> str:
        """Looks up the speech-optimized pronunciation representation for a single term."""
        lang = (language or "en-IN").lower()
        if not lang.startswith("en"):
            return term
        for eng_phrase, dev_target in self.lexicon:
            if eng_phrase.lower() == term.lower():
                return dev_target
        return term


pronunciation_service = PronunciationService()
