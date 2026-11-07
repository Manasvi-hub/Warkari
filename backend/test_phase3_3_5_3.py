"""Focused test suite for Phase 3.3.5.3: Critical Reliability Fixes.

Verifies:
1. Informational helpline inquiries in all 3 languages (EN, MR, HI):
   - Classified as INTENT_HELPLINE_INFO.
   - Contains 108 / १०८.
   - Zero incident tickets created.
2. Active life-safety emergencies in all 3 languages:
   - Classified as INTENT_EMERGENCY.
   - Contains 108 / १०८.
   - Creates incident ticket only when appropriate.
3. Speech normalization & single 108 rule:
   - Number 108 / १०८ appears exactly once in spoken text.
4. Database integrity:
   - 5 facilities intact.
   - Incidents count preserved.
   - Foreign key integrity valid.
"""

import sqlite3
import pytest
from backend.services.intent_service import intent_service, INTENT_HELPLINE_INFO, INTENT_EMERGENCY
from backend.services.response_service import build_response_for_intent
from backend.services.assistant_service import assistant_service
from backend.services.speech_normalization_service import speech_normalization_service
from backend.database import SessionLocal


def test_helpline_info_intent_classification():
    cases = [
        ("What is the emergency ambulance number?", "en-IN"),
        ("What number should I call in a medical emergency?", "en-IN"),
        ("What is 108?", "en-IN"),
        ("आपत्कालीन परिस्थितीत कोणत्या नंबरवर फोन करावा?", "mr-IN"),
        ("रुग्णवाहिका नंबर काय आहे?", "mr-IN"),
        ("आपातकालीन स्थिति में एम्बुलेंस के लिए किस नंबर पर कॉल करें?", "hi-IN"),
        ("इमरजेंसी में किस नंबर पर संपर्क करें?", "hi-IN")
    ]
    for q, lang in cases:
        res = intent_service.classify_intent(q, language_hint=lang)
        assert res.intent == INTENT_HELPLINE_INFO, f"Expected HELPLINE_INFO for '{q}', got {res.intent}"
        assert res.is_emergency is False, f"Helpline inquiry '{q}' should not be marked active emergency"


def test_helpline_info_no_incident_creation():
    with SessionLocal() as db:
        # Check initial incident count
        conn = sqlite3.connect("warkari.db")
        c = conn.cursor()
        c.execute("SELECT count(*) FROM incidents")
        initial_count = c.fetchone()[0]
        conn.close()

        queries = [
            ("What is the emergency ambulance number?", "en-IN"),
            ("आपत्कालीन परिस्थितीत कोणत्या नंबरवर फोन करावा?", "mr-IN"),
            ("आपातकालीन स्थिति में एम्बुलेंस के लिए किस नंबर पर कॉल करें?", "hi-IN")
        ]

        for q, lang in queries:
            res = assistant_service.process_chat(db=db, message=q, language=lang)
            assert res["intent"] == INTENT_HELPLINE_INFO
            assert res["incident"] is None, f"Query '{q}' should NOT create an incident!"
            assert "108" in res["response_text"] or "१०८" in res["response_text"]

            # Speech check: exactly one 108
            speech = res["speech_text"]
            assert speech is not None
            if lang.startswith("mr") or lang.startswith("hi"):
                assert speech.count("१०८") == 1, f"Expected exactly one १०८ in speech for '{q}', got: {speech}"
            else:
                assert speech.count("108") == 1, f"Expected exactly one 108 in speech for '{q}', got: {speech}"

        # Assert no incidents were added to SQLite
        conn = sqlite3.connect("warkari.db")
        c = conn.cursor()
        c.execute("SELECT count(*) FROM incidents")
        final_count = c.fetchone()[0]
        conn.close()
        assert final_count == initial_count, f"Incident count changed from {initial_count} to {final_count} during helpline queries!"


def test_active_emergency_creates_incident_and_contains_108():
    with SessionLocal() as db:
        queries = [
            ("Someone is unconscious need urgent help", "en-IN"),
            ("एक वारकरी चक्कर येऊन बेशुद्ध पडले आहेत, तातडीने मदत हवी", "mr-IN"),
            ("कोई व्यक्ति बेहोश हो गया है तुरंत मदद चाहिए", "hi-IN")
        ]
        for q, lang in queries:
            res = assistant_service.process_chat(db=db, message=q, language=lang)
            assert res["intent"] == INTENT_EMERGENCY
            assert res["incident"] is not None, f"Active emergency '{q}' MUST create an incident!"
            assert "108" in res["response_text"] or "१०८" in res["response_text"]

            speech = res["speech_text"]
            if lang.startswith("mr") or lang.startswith("hi"):
                assert speech.count("१०८") == 1, f"Expected exactly one १०८ in emergency speech for '{q}', got: {speech}"
            else:
                assert speech.count("108") == 1, f"Expected exactly one 108 in emergency speech for '{q}', got: {speech}"


def test_database_integrity():
    conn = sqlite3.connect("warkari.db")
    c = conn.cursor()
    c.execute("SELECT count(*) FROM facilities")
    assert c.fetchone()[0] == 5
    c.execute("PRAGMA foreign_key_check")
    assert len(c.fetchall()) == 0
    conn.close()


if __name__ == "__main__":
    test_helpline_info_intent_classification()
    test_helpline_info_no_incident_creation()
    test_active_emergency_creates_incident_and_contains_108()
    test_database_integrity()
    print("ALL Phase 3.3.5.3 Tests PASSED successfully!")

