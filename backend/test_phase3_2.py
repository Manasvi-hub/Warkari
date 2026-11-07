"""Test suite for Phase 3.2: Intelligent Context-Aware Response Engine & Voice Pipeline.
"""
import sys
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from backend.database import SessionLocal, init_db
from backend.services.assistant_service import assistant_service
from backend.services.response_service import build_response_for_intent
from backend.services.facility_service import facility_service


def test_phase3_2():
    init_db()

    db = SessionLocal()
    try:
        print("\n--- TEST 1: Nuance Distinction for Medical vs Emergency ---")
        # 1. Routine medical check
        res_med = assistant_service.process_chat(db, "प्रथमोपचार केंद्र कुठे आहे?", language="mr-IN")
        print("Routine Medical Intent:", res_med["intent"])
        print("Response:", res_med["response_text"][:80], "...")
        assert res_med["intent"] == "MEDICAL"
        assert res_med["incident"] is None, "Routine medical query should not automatically file critical incident"

        # 2. Medical collapse emergency
        res_emerg = assistant_service.process_chat(db, "एक वारकरी चक्कर येऊन बेशुद्ध पडले आहेत, तातडीने मदत हवी", language="mr-IN")
        print("\nEmergency Intent:", res_emerg["intent"])
        print("Incident Created:", res_emerg["incident"] is not None)
        print("Response:", res_emerg["response_text"][:100], "...")
        assert res_emerg["intent"] in ["EMERGENCY", "MEDICAL"]
        assert res_emerg["incident"] is not None, "Critical emergency query should file high-urgency incident"
        assert "१०८" in res_emerg["response_text"] or "108" in res_emerg["response_text"], "Emergency medical response must reference 108 ambulance"

        print("\n--- TEST 2: Nuance Distinction for Food ---")
        # Prasad vs Meal
        res_prasad = assistant_service.process_chat(db, "प्रसाद वाटप कधी आणि कुठे होणार आहे?", language="mr-IN")
        print("Prasad Intent:", res_prasad["intent"])
        print("Response:", res_prasad["response_text"][:80], "...")
        assert "प्रसाद" in res_prasad["response_text"]

        res_meal = assistant_service.process_chat(db, "अन्नछत्र कुठे आहे जेवणासाठी?", language="mr-IN")
        print("\nMeal Intent:", res_meal["intent"])
        print("Response:", res_meal["response_text"][:80], "...")
        assert "अन्नछत्र" in res_meal["response_text"]

        print("\n--- TEST 3: Nuance Distinction for Sanitation ---")
        # Restroom search vs hygiene issue
        res_toilet = assistant_service.process_chat(db, "जवळचे शौचालय कुठे आहे?", language="mr-IN")
        print("Sanitation Search Response:", res_toilet["response_text"][:80], "...")
        assert res_toilet["incident"] is None

        res_dirty = assistant_service.process_chat(db, "येथील स्वच्छतागृह अतिशय अस्वच्छ आहे आणि दुर्गंधी येत आहे", language="mr-IN")
        print("\nSanitation Complaint Response:", res_dirty["response_text"][:80], "...")
        assert res_dirty["incident"] is not None, "Hygiene complaint should register ticket for sanitation team"

        print("\n--- TEST 4: Multilingual Consistency (Hindi and English) ---")
        res_hi = assistant_service.process_chat(db, "पीने का पानी कहाँ मिलेगा?", language="hi-IN")
        print("Hindi Water Response:", res_hi["response_text"][:80], "...")
        assert "पेयजल" in res_hi["response_text"] or "पानी" in res_hi["response_text"]
        # Ensure pure Hindi template phrasing
        assert "आमच्या" not in res_hi["response_text"] and "खात्री करा" not in res_hi["response_text"]

        res_en = assistant_service.process_chat(db, "Where can I get drinking water?", language="en-IN")
        print("English Water Response:", res_en["response_text"][:80], "...")
        assert "water" in res_en["response_text"].lower()

        print("\n--- TEST 5: Distance Calculation Integrity ---")
        # With GPS coordinates
        res_gps = assistant_service.process_chat(db, "पिण्याचे पाणी कुठे आहे?", language="mr-IN", user_lat=18.5204, user_lon=73.8567)
        fac_gps = res_gps["facilities"][0]
        print(f"Facility with GPS: {fac_gps['name']}, distance: {fac_gps['distance_km']} km")
        assert fac_gps["distance_km"] is not None

        # Without GPS coordinates
        res_no_gps = assistant_service.process_chat(db, "पिण्याचे पाणी कुठे आहे?", language="mr-IN", user_lat=None, user_lon=None)
        fac_no_gps = res_no_gps["facilities"][0]
        print(f"Facility without GPS: {fac_no_gps['name']}, distance: {fac_no_gps['distance_km']}")
        assert fac_no_gps["distance_km"] is None, "Distance must be None when GPS is not provided"

        print("\n ALL TESTS PASSED SUCCESSFULLY! Phase 3.2 requirements fully satisfied.")
    finally:
        db.close()


if __name__ == "__main__":
    test_phase3_2()
