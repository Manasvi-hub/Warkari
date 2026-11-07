"""Speech Normalization Service for Warkari Pilgrimage Platform.

Performs clean separation between:
- `display_text`: The formatted, readable markdown/text shown in the React UI.
- `speech_text`: Clean, natural, spoken text sent to Gnani Timbre TTS v2.5.

Ensures:
1. No duplicate emergency numbers (e.g. removes redundant '१०८ (108)' dual notation).
2. Clean spoken representation of ticket numbers and IDs.
3. Pronunciation optimization of Indian pilgrimage places via PronunciationService.
4. Stripping of UI markdown tags, brackets, and bullet symbols that sound robotic when read aloud.
5. Removal of redundant disclaimers or repeated phrases without removing safety content.
"""

import re
from typing import Optional
from backend.services.pronunciation_service import pronunciation_service


class SpeechNormalizationService:
    """Normalizes response text specifically for natural voice output."""

    def normalize_for_speech(self, text: str, language: str = "mr-IN") -> str:
        """Converts display text into high-quality, natural spoken text for Gnani Timbre."""
        if not text:
            return ""

        lang = (language or "mr-IN").lower()
        speech = text

        # 1. Deduplicate Dual Emergency Numbers: "१०८ (108)" or "108 (१०८)"
        # For Marathi: keep "१०८"
        # For Hindi: keep "१०८"
        # For English: keep "108"
        speech = self._normalize_emergency_numbers(speech, lang)

        # 2. Normalize Ticket/ID numbers for natural speech
        # e.g., "तिकीट #31" -> "तिकीट क्रमांक ३१" (mr) or "टिकट नंबर 31" (hi/en)
        speech = self._normalize_ticket_ids(speech, lang)

        # 3. Clean UI Markdown & Bullet Formatting, converting badges to natural spoken warnings
        speech = self._strip_ui_formatting(speech, lang=lang)

        # 3.1. Language-Specific Bilingual Deduplication:
        # In Marathi responses, remove parenthetical English annotations like '(Medical Camp)', '(Pandharpur Entry Gate)'
        # to avoid speaking both Marathi and English names for the same facility.
        speech = self._deduplicate_bilingual_names(speech, lang=lang)

        # 4. Apply Place-Name Pronunciation Dictionary
        target_lang = "mr-IN" if lang.startswith("mr") else "hi-IN" if lang.startswith("hi") else "en-IN"
        speech = pronunciation_service.apply_pronunciation_to_text(speech, language=target_lang)

        # 5. Clean whitespace and duplicate punctuation
        speech = re.sub(r"\s+", " ", speech).strip()
        speech = re.sub(r"([.!?,])\1+", r"\1", speech)

        return speech

    def _deduplicate_bilingual_names(self, text: str, lang: str) -> str:
        """Removes redundant bilingual parenthetical text that causes duplicate spoken names."""
        if lang.startswith("mr") or lang.startswith("hi"):
            # If the response is in Marathi or Hindi, strip English parentheticals:
            # e.g., 'आरोग्य शिबिर (Medical Camp)' -> 'आरोग्य शिबिर'
            # 'पंढरपूर प्रवेशद्वार (Pandharpur Entry Gate)' -> 'पंढरपूर प्रवेशद्वार'
            # 'वाखरी मुक्काम तळ (Wakhari Halt)' -> 'वाखरी मुक्काम तळ'
            text = re.sub(r"\s*\([A-Za-z0-9\s,\.\-&/]+\)", "", text)
        return text

    def _normalize_emergency_numbers(self, text: str, lang: str) -> str:
        """Removes duplicate dual-written emergency contact numbers like '१०८ (108)'."""
        if lang.startswith("mr") or lang.startswith("hi"):
            # Replace dual occurrences with single Devanagari representation
            text = re.sub(r"१०८\s*\(\s*108\s*\)", "१०८", text)
            text = re.sub(r"108\s*\(\s*१०८\s*\)", "१०८", text)
            text = re.sub(r"\b108\b", "१०८", text)
            # Remove repeated contiguous occurrences: "१०८ १०८"
            text = re.sub(r"१०८(\s+१०८)+", "१०८", text)
        else:
            # English: Replace with single Arabic numeral "108"
            text = re.sub(r"१०८\s*\(\s*108\s*\)", "108", text)
            text = re.sub(r"108\s*\(\s*१०८\s*\)", "108", text)
            text = re.sub(r"\b१०८\b", "108", text)
            text = re.sub(r"108(\s+108)+", "108", text)

        return text

    def _normalize_ticket_ids(self, text: str, lang: str) -> str:
        """Converts ticket symbols like '#31' into natural spoken phrases."""
        if lang.startswith("mr"):
            # 'तिकीट #31' -> 'तिकीट क्रमांक 31'
            text = re.sub(r"तिकीट\s*#(\d+)", r"तिकीट क्रमांक \1", text)
        elif lang.startswith("hi"):
            # 'टिकट #31' -> 'टिकट नंबर 31'
            text = re.sub(r"टिकट\s*#(\d+)", r"टिकट नंबर \1", text)
        else:
            # 'Ticket #31' -> 'Ticket number 31'
            text = re.sub(r"Ticket\s*#(\d+)", r"Ticket number \1", text, flags=re.IGNORECASE)
            text = re.sub(r"request\s*#(\d+)", r"request number \1", text, flags=re.IGNORECASE)

        return text

    def _strip_ui_formatting(self, text: str, lang: str = "mr-IN") -> str:
        """Removes UI-only symbols like list bullets, bold asterisks, and brackets while converting demo/verification badges to spoken warnings."""
        # Convert demo data notices to natural spoken warnings instead of deleting them
        if lang.startswith("mr"):
            demo_spoken = " ही प्रात्यक्षिक डेमो माहिती असून प्रत्यक्ष जागेवर याची पडताळणी झालेली नाही. "
            text = re.sub(r"\[डेमो डेटा[^\]]*\]", demo_spoken, text)
            text = re.sub(r"\(डेमो डेटा[^)]*\)", demo_spoken, text)
            text = re.sub(r"\[Demo Data[^\]]*\]", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(Note: this is synthetic demo data[^)]*\)", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(पडताळलेले केंद्र\)", " ही अधिकृत पडताळलेली सुविधा आहे. ", text)
        elif lang.startswith("hi"):
            demo_spoken = " यह केवल प्रदर्शन डेमो डेटा है और वास्तविक रूप से सत्यापित नहीं है। "
            text = re.sub(r"\[डेमो डेटा[^\]]*\]", demo_spoken, text)
            text = re.sub(r"\(डेमो डेटा[^)]*\)", demo_spoken, text)
            text = re.sub(r"\[Demo Data[^\]]*\]", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(Note: this is synthetic demo data[^)]*\)", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(सत्यापित केंद्र\)", " यह सत्यापित सुविधा है। ", text)
        else:
            demo_spoken = " Please note, this is demonstration data and has not been verified in the real world. "
            text = re.sub(r"\[डेमो डेटा[^\]]*\]", demo_spoken, text)
            text = re.sub(r"\(डेमो डेटा[^)]*\)", demo_spoken, text)
            text = re.sub(r"\[Demo Data[^\]]*\]", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(Note: this is synthetic demo data[^)]*\)", demo_spoken, text, flags=re.IGNORECASE)
            text = re.sub(r"\(Verified Facility\)", " This is an officially verified facility. ", text, flags=re.IGNORECASE)

        # Remove bold/italic markdown (**text**, *text*)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)

        # Remove list enumeration markers at line starts: "1. ", "2. "
        text = re.sub(r"^\s*\d+\.\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n\s*\d+\.\s*", ". ", text)

        # Replace newlines with full stops or spaces
        text = re.sub(r"\n+", ". ", text)

        # Remove remaining square brackets
        text = text.replace("[", "").replace("]", "")
        # Remove empty parentheses
        text = re.sub(r"\(\s*\)", "", text)

        return text


speech_normalization_service = SpeechNormalizationService()

