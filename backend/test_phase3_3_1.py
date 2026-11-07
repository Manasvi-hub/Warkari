"""Test suite for Phase 3.3.1:
Frontend Audio Playback Fix, Multilingual Native Devanagari Pronunciation & Regression.
"""

import sys
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from backend.database import SessionLocal, init_db
from backend.services.assistant_service import assistant_service
from backend.services.pronunciation_service import pronunciation_service
from backend.services.speech_normalization_service import speech_normalization_service
from backend.services.voice_service import voice_service


def test_phase3_3_1():
    init_db()
    db = SessionLocal()

    print("\n============================================================")
    print("PHASE 3.3.1: FRONTEND AUDIO & MULTILINGUAL PRONUNCIATION TESTS")
    print("============================================================")

    try:
        # -------------------------------------------------------------
        # TEST 1: Native Devanagari Substitution for English Speech
        # -------------------------------------------------------------
        print("\n--- TEST 1: Native Devanagari Substitution for English Speech ---")
        palkhi_places = [
            ("Pandharpur", "पंढरपूर"),
            ("Wakhari", "वाखरी"),
            ("Saswad", "सासवड"),
            ("Jejuri", "जेजुरी"),
            ("Lonand", "लोणंद"),
            ("Phaltan", "फलटण"),
            ("Velapur", "वेळापूर"),
            ("Chandrabhaga", "चंद्रभागा"),
            ("Dehu", "देहू"),
            ("Alandi", "आळंदी"),
        ]

        display_text = "Welcome to Pandharpur. The next halt is Wakhari near Chandrabhaga river."
        spoken_en = pronunciation_service.apply_pronunciation_to_text(display_text, language="en-IN")

        print(f"[Display Text] : {display_text}")
        print(f"[English Spoken]: {spoken_en}")

        # English speech must contain native Devanagari spellings
        assert "पंढरपूर" in spoken_en, "Pandharpur should be substituted with पंढरपूर in en-IN speech"
        assert "वाखरी" in spoken_en, "Wakhari should be substituted with वाखरी in en-IN speech"
        assert "चंद्रभागा" in spoken_en, "Chandrabhaga should be substituted with चंद्रभागा in en-IN speech"
        # Display text must remain strictly English Latin
        assert "Pandharpur" in display_text
        assert "Wakhari" in display_text
        assert "Chandrabhaga" in display_text

        # Verify all 10 locations in en-IN
        for eng_name, dev_script in palkhi_places:
            test_sentence = f"Palkhi halt at {eng_name} camp."
            subbed = pronunciation_service.apply_pronunciation_to_text(test_sentence, language="en-IN")
            print(f"'{eng_name}' -> '{subbed}'")
            assert dev_script in subbed, f"Expected '{dev_script}' in '{subbed}' for en-IN"
            assert eng_name not in subbed, f"English name '{eng_name}' should be replaced in en-IN speech"

        # -------------------------------------------------------------
        # TEST 2: Marathi & Hindi Unchanged by English Pronunciation Rules
        # -------------------------------------------------------------
        print("\n--- TEST 2: Marathi and Hindi Text Unchanged by en-IN Rules ---")
        mr_input = "पंढरपूर विठ्ठल रुक्मिणी मंदिर आणि वाखरी मुक्काम तळ."
        mr_processed = pronunciation_service.apply_pronunciation_to_text(mr_input, language="mr-IN")
        assert mr_processed == mr_input, "Marathi text should remain unaltered"

        hi_input = "पंढरपुर श्री विट्ठल रुक्मिणी मंदिर और वाखरी पड़ाव।"
        hi_processed = pronunciation_service.apply_pronunciation_to_text(hi_input, language="hi-IN")
        assert hi_processed == hi_input, "Hindi text should remain unaltered"

        # -------------------------------------------------------------
        # TEST 3: Partial Word Immunity (No Unintended Replacements)
        # -------------------------------------------------------------
        print("\n--- TEST 3: Partial Word Immunity ---")
        unrelated_sentence = "The student wants to expand his horizon."
        # 'expand' contains 'and', ensure no partial word replacement occurs
        safe_out = pronunciation_service.apply_pronunciation_to_text(unrelated_sentence, language="en-IN")
        assert safe_out == unrelated_sentence, f"Partial word was corrupted: {safe_out}"

        # -------------------------------------------------------------
        # TEST 4: Single Spoken 108 in Emergency (Audio & Text)
        # -------------------------------------------------------------
        print("\n--- TEST 4: Single Spoken 108 & Safety Disclosures ---")
        res_emerg = assistant_service.process_chat(db, "एक वारकरी बेशुद्ध पडले आहेत तातडीने मदत हवी", language="mr-IN")
        spk_mr = res_emerg["speech_text"]
        print(f"[Marathi Emergency Spoken]: {spk_mr}")
        assert spk_mr.count("१०८") == 1, f"Expected 108 spoken once, got {spk_mr.count('१०८')}"
        assert "108" not in spk_mr
        assert "हे थेट पोलीस किंवा आपत्कालीन कॉल नाही" in spk_mr, "Safety disclaimer must be preserved"

        # -------------------------------------------------------------
        # TEST 5: Spoken Demo Data Safety Disclosure Intact
        # -------------------------------------------------------------
        print("\n--- TEST 5: Spoken Demo Data Disclosure Intact ---")
        res_fac = assistant_service.process_chat(db, "पिण्याचे पाणी कुठे मिळेल?", language="mr-IN")
        print(f"[Marathi Demo Spoken]: {res_fac['speech_text'][:100]}...")
        assert "डेमो" in res_fac["speech_text"] or "पडताळणी" in res_fac["speech_text"], "Demo safety warning must be in spoken response"

        # -------------------------------------------------------------
        # TEST 6: Live Timbre v2.5 Audio Synthesis of Devanagari in en-IN
        # -------------------------------------------------------------
        print("\n--- TEST 6: Live Timbre Audio Synthesis of Devanagari in en-IN ---")
        en_audio_text = "Welcome to पंढरपूर. The next halt is वाखरी."
        audio_bytes, mime = voice_service.synthesize_speech(en_audio_text, language="en-IN", voice="Nalini")
        print(f"Generated en-IN audio: {len(audio_bytes)} bytes | MIME: {mime}")
        assert len(audio_bytes) > 20000, "Audio response truncated or empty"

        print("\n ALL PHASE 3.3.1 TESTS PASSED SUCCESSFULLY!")

    finally:
        db.close()


if __name__ == "__main__":
    test_phase3_3_1()

