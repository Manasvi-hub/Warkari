"""Comprehensive Test Matrix for Phase 3.3:
Speech Normalization, Pronunciation Dictionary & Natural Voice Refinement.
"""

import sys
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from backend.database import SessionLocal, init_db
from backend.services.assistant_service import assistant_service
from backend.services.speech_normalization_service import speech_normalization_service
from backend.services.pronunciation_service import pronunciation_service
from backend.services.voice_service import voice_service


def test_phase3_3():
    init_db()
    db = SessionLocal()

    print("\n========================================================")
    print("PHASE 3.3: SPEECH NORMALIZATION & PRONUNCIATION TESTS")
    print("========================================================")

    try:
        # -----------------------------------------------------------
        # TEST 1: Number Repetition & Emergency 108 Normalization
        # -----------------------------------------------------------
        print("\n--- TEST 1: Number Repetition & Single 108 Representation ---")

        # Marathi Emergency
        res_mr = assistant_service.process_chat(db, "एक वारकरी बेशुद्ध पडले आहेत तातडीने मदत हवी", language="mr-IN")
        disp_mr = res_mr["response_text"]
        spk_mr = res_mr["speech_text"]

        print(f"[Marathi Display]: {disp_mr}")
        print(f"[Marathi Speech] : {spk_mr}")
        # Verify single 108 representation in spoken text
        assert "१०८ (108)" not in spk_mr, "Dual notation '१०८ (108)' must be absent in speech text"
        assert spk_mr.count("१०८") == 1, f"Expected 108 spoken exactly once in Marathi, got {spk_mr.count('१०८')}"
        assert "108" not in spk_mr, "English digits 108 should not appear in Marathi speech"

        # Hindi Emergency
        res_hi = assistant_service.process_chat(db, "एक तीर्थयात्री बेहोश हो गए हैं तुरंत आपातकालीन मदद चाहिए", language="hi-IN")
        disp_hi = res_hi["response_text"]
        spk_hi = res_hi["speech_text"]

        print(f"\n[Hindi Display]: {disp_hi}")
        print(f"[Hindi Speech] : {spk_hi}")
        assert "१०८ (108)" not in spk_hi
        assert spk_hi.count("१०८") == 1, f"Expected 108 spoken exactly once in Hindi, got {spk_hi.count('१०८')}"
        assert "108" not in spk_hi

        # English Emergency
        res_en = assistant_service.process_chat(db, "A pilgrim collapsed unconscious need emergency assistance immediately", language="en-IN")
        disp_en = res_en["response_text"]
        spk_en = res_en["speech_text"]

        print(f"\n[English Display]: {disp_en}")
        print(f"[English Speech] : {spk_en}")
        assert "१०८" not in spk_en, "Devanagari numerals should not be present in English speech"
        assert spk_en.count("108") == 1, f"Expected 108 spoken exactly once in English, got {spk_en.count('108')}"

        # -----------------------------------------------------------
        # TEST 2: Duplicate Instructions & Disclaimers Prevention
        # -----------------------------------------------------------
        print("\n--- TEST 2: Duplicate Instructions & Disclaimers Prevention ---")
        # Check disclaimer counts
        disclaimer_mr_phrase = "हे थेट पोलीस किंवा आपत्कालीन कॉल नाही"
        assert spk_mr.count(disclaimer_mr_phrase) <= 1, "Police disclaimer must not be duplicated"

        # Check ticket number conversion
        assert "#" not in spk_mr, "Spoken text should not contain raw '#' symbol"
        assert "क्रमांक" in spk_mr or "नंबर" in spk_mr, "Ticket ID should be naturally spoken with word prefix"

        # -----------------------------------------------------------
        # TEST 3: Pronunciation Dictionary & Place Name Transformation
        # -----------------------------------------------------------
        print("\n--- TEST 3: Pronunciation Dictionary & Display vs Spoken Form ---")
        test_places = [
            ("Pandharpur", "en-IN", "पंढरपूर"),
            ("Wakhari", "en-IN", "वाखरी"),
            ("Chandrabhaga", "en-IN", "चंद्रभागा"),
            ("Pune", "en-IN", "पुणे"),
            ("Saswad", "en-IN", "सासवड"),
            ("Jejuri", "en-IN", "जेजुरी"),
            ("Velapur", "en-IN", "वेळापूर"),
            ("Dehu", "en-IN", "देहू"),
        ]

        for word, lang, expected_phonetic in test_places:
            norm = pronunciation_service.apply_pronunciation_to_text(f"Welcome to {word} station.", language=lang)
            print(f"[{lang}] '{word}' -> '{norm}'")
            assert expected_phonetic in norm, f"Expected phonetic '{expected_phonetic}' in '{norm}'"

        # -----------------------------------------------------------
        # TEST 4: Live Audio Generation & Actual Audio Output Check
        # -----------------------------------------------------------
        print("\n--- TEST 4: Live Timbre v2.5 Audio Output Generation ---")
        audio_samples = [
            ("Pandharpur_EN", "Welcome to Pundharpoor sacred temple.", "en-IN"),
            ("Pandharpur_MR", "पंढरपूर विठ्ठल रुक्मिणी मंदिरात आपले स्वागत आहे.", "mr-IN"),
            ("Pandharpur_HI", "पंढरपुर श्री विट्ठल रुक्मिणी मंदिर में आपका स्वागत है।", "hi-IN"),
            ("Wakhari_EN", "Water tankers are stationed at Waakharee halt.", "en-IN"),
            ("Wakhari_MR", "वाखरी मुक्काम तळावर पाण्याची सोय आहे.", "mr-IN"),
            ("Chandrabhaga_EN", "Holy bath at Chundrabhaga river ghat.", "en-IN"),
            ("Chandrabhaga_MR", "चंद्रभागा नदीच्या पवित्र तीरावर स्नान व्यवस्था आहे.", "mr-IN"),
        ]

        for label, text, lang in audio_samples:
            audio_bytes, mime = voice_service.synthesize_speech(text, language=lang)
            print(f"Sample '{label}' ({lang}): {len(audio_bytes)} bytes | MIME: {mime}")
            assert len(audio_bytes) > 20000, f"Audio sample {label} was truncated or too small ({len(audio_bytes)} bytes)"

        # -----------------------------------------------------------
        # TEST 5: Regression & Safety Integrity
        # -----------------------------------------------------------
        print("\n--- TEST 5: Regression & Safety Integrity Verification ---")
        # 1. Missing Person Workflow
        mp_res = assistant_service.process_chat(db, "माझे वडील हरवले आहेत", language="mr-IN")
        assert mp_res["awaiting_missing_person_consent"] is True
        assert mp_res["speech_text"] is not None
        assert "मदत नोंदणी" in mp_res["speech_text"]

        # 2. Routine Medical Query (No false emergency)
        med_res = assistant_service.process_chat(db, "प्रथमोपचार केंद्र कुठे आहे?", language="mr-IN")
        assert med_res["intent"] == "MEDICAL"
        assert med_res["incident"] is None
        assert "प्रथमोपचार" in med_res["speech_text"]

        # 3. Clean separation preserved
        assert res_mr["response_text"] is not None
        assert res_mr["speech_text"] is not None
        assert res_mr["response_text"] != res_mr["speech_text"], "Display text and speech text should be cleanly separated"

        # -----------------------------------------------------------
        # TEST 6: Spoken Demo Data Safety Disclosure Test (Phase 3.3 Safety Correction)
        # -----------------------------------------------------------
        print("\n--- TEST 6: Spoken Demo Data Warning Preservation ---")

        # Marathi Demo Facility Query (Water)
        res_fac_mr = assistant_service.process_chat(db, "पिण्याचे पाणी कुठे मिळेल?", language="mr-IN")
        print(f"[Marathi Demo Display]: {res_fac_mr['response_text'][:90]}...")
        print(f"[Marathi Demo Speech] : {res_fac_mr['speech_text'][:90]}...")
        # Check that demo warning is NOT removed from speech_text
        assert "डेमो" in res_fac_mr["speech_text"] or "पडताळणी" in res_fac_mr["speech_text"], (
            "SAFETY VIOLATION: Spoken Marathi response must explicitly disclose demo/unverified data to listeners!"
        )

        # Hindi Demo Facility Query
        res_fac_hi = assistant_service.process_chat(db, "पीने का पानी कहाँ मिलेगा?", language="hi-IN")
        print(f"\n[Hindi Demo Display]: {res_fac_hi['response_text'][:90]}...")
        print(f"[Hindi Demo Speech] : {res_fac_hi['speech_text'][:90]}...")
        assert "डेमो" in res_fac_hi["speech_text"] or "सत्यापित" in res_fac_hi["speech_text"], (
            "SAFETY VIOLATION: Spoken Hindi response must explicitly disclose demo/unverified data to listeners!"
        )

        # English Demo Facility Query
        res_fac_en = assistant_service.process_chat(db, "Where can I get drinking water?", language="en-IN")
        print(f"\n[English Demo Display]: {res_fac_en['response_text'][:90]}...")
        print(f"[English Demo Speech] : {res_fac_en['speech_text'][:90]}...")
        assert "demo" in res_fac_en["speech_text"].lower() or "verified" in res_fac_en["speech_text"].lower(), (
            "SAFETY VIOLATION: Spoken English response must explicitly disclose demo/unverified data to listeners!"
        )

        print("\n ALL PHASE 3.3 TESTS COMPLETED AND VERIFIED SUCCESSFULLY!")

    finally:
        db.close()


if __name__ == "__main__":
    test_phase3_3()

