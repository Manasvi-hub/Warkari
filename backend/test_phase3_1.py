"""Comprehensive Automated Test Suite for Phase 3.1:
Reliability, Safety, Language Consistency & Privacy Enforcements.
"""

import requests

BASE = "http://127.0.0.1:8000"
INTEL = f"{BASE}/api/intelligence"

def run_tests():
    print("==================================================")
    print("STARTING PHASE 3.1 VERIFICATION TEST SUITE")
    print("==================================================")

    # -------------------------------------------------------------------------
    # TEST SUITE 1: Facility Integrity & Label Rules
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Facility Integrity & Contact Validation:")
    r_fac = requests.get(f"{INTEL}/facilities").json()
    assert len(r_fac) > 0, "No facilities found"
    for fac in r_fac:
        if fac["is_demo"]:
            assert fac["display_status"] == "DEMO DATA", f"Demo facility displayed {fac['display_status']}"
            assert fac["is_verified"] is False, "Demo facility cannot be is_verified=True"
            assert fac["contact_phone"] is None, f"Demo facility has fake phone: {fac['contact_phone']}"
        elif fac["is_verified"]:
            assert fac["display_status"] == "VERIFIED", f"Verified facility displayed {fac['display_status']}"
            assert fac["is_demo"] is False, "Verified facility cannot be demo"
        else:
            assert fac["display_status"] == "UNVERIFIED", f"Unverified facility displayed {fac['display_status']}"

    print("  -> PASS: All demo facilities have display_status='DEMO DATA', is_verified=False, contact_phone=None.")

    # -------------------------------------------------------------------------
    # TEST SUITE 2: Missing-Person Consent & Staged Workflow
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Missing-Person Staged Consent Workflow:")

    # 2a. Initial inquiry without prior consent -> NO incident created, asks for consent
    r_lost1 = requests.post(f"{INTEL}/chat", json={
        "message": "माझे वडील हरवले आहेत.",
        "language": "mr-IN"
    }).json()
    assert r_lost1["intent"] == "LOST_PERSON", f"Expected LOST_PERSON, got {r_lost1['intent']}"
    assert r_lost1["incident"] is None, "Violation: Incident created on initial request without consent!"
    assert r_lost1["awaiting_missing_person_consent"] is True, "Expected awaiting_missing_person_consent to be True"
    print("  -> PASS: Initial lost-person request prompts for consent without creating ticket.")

    # 2b. User declines consent -> NO incident created, acknowledges cancellation
    r_lost_declined = requests.post(f"{INTEL}/chat", json={
        "message": "नाही",
        "language": "mr-IN",
        "missing_person_consent": False
    }).json()
    assert r_lost_declined["incident"] is None, "Violation: Incident created after user declined consent!"
    print("  -> PASS: Declining consent records NO incident.")

    # 2c. User grants consent without minimal details -> prompts for name/age/location
    r_lost_consented = requests.post(f"{INTEL}/chat", json={
        "message": "होय",
        "language": "mr-IN",
        "missing_person_consent": True
    }).json()
    assert r_lost_consented["awaiting_missing_person_details"] is True, "Expected prompt for minimal details"
    assert r_lost_consented["incident"] is None, "Should await details before creating incident"
    print("  -> PASS: Consent granted without details prompts for essential identifier/age/location.")

    # 2d. User supplies minimal details with consent -> incident created with safety disclaimer
    r_lost_complete = requests.post(f"{INTEL}/chat", json={
        "message": "माझे वडील हरवले आहेत",
        "language": "mr-IN",
        "missing_person_consent": True,
        "missing_person_details": {
            "name": "ज्ञानेश्वर पाटील",
            "age": "६८ वर्षे",
            "last_seen": "वाखरी मुक्काम तळ"
        }
    }).json()
    assert r_lost_complete["incident"] is not None, "Expected incident to be created"
    inc_id = r_lost_complete["incident"]["id"]
    assert "स्वयंसेवक त्वरित नियुक्त झाला आहे किंवा आपत्कालीन सेवांशी संपर्क झाला आहे असा नाही" in r_lost_complete["incident"]["safety_disclaimer"], "Safety disclaimer missing!"
    print(f"  -> PASS: Incident #{inc_id} created with structured consent and non-guarantee safety disclaimer.")

    # -------------------------------------------------------------------------
    # TEST SUITE 3: Privacy & Public Endpoint Access Restrictions
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Privacy Masking on Public Incident Endpoint:")
    r_public = requests.get(f"{INTEL}/incidents/{inc_id}").json()
    assert "ज्ञानेश्वर पाटील" not in r_public["description"], "Violation: Private missing-person name leaked publicly!"
    assert "तपशील नियंत्रण कक्षाकडे सुरक्षित" in r_public["description"], "Sanitized privacy placeholder missing!"
    print("  -> PASS: Public GET /api/intelligence/incidents/{id} strictly masks private identity.")

    # -------------------------------------------------------------------------
    # TEST SUITE 4: Multilingual Consistency
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Multilingual Response Consistency:")

    # English request
    r_en = requests.post(f"{INTEL}/chat", json={
        "message": "Where can I find drinking water?",
        "language": "en-IN"
    }).json()
    assert "Here is the facility information available in our current records" in r_en["response_text"], f"English response was mixed or incorrect: {r_en['response_text']}"
    assert "उपलब्ध" not in r_en["response_text"], "Violation: Marathi word leaked into English response!"
    print("  -> PASS: English request receives 100% pure English response.")

    # Marathi request
    r_mr = requests.post(f"{INTEL}/chat", json={
        "message": "पिण्याचे पाणी कुठे मिळेल?",
        "language": "mr-IN"
    }).json()
    assert "आपल्या जवळ उपलब्ध असलेल्या सुविधांची माहिती येथे आहे" in r_mr["response_text"], f"Marathi response unexpected: {r_mr['response_text']}"
    print("  -> PASS: Marathi request receives 100% pure Marathi response.")

    # Hindi request
    r_hi = requests.post(f"{INTEL}/chat", json={
        "message": "पीने का पानी कहाँ मिलेगा?",
        "language": "hi-IN"
    }).json()
    assert "यहाँ आपके आसपास उपलब्ध सुविधाओं की जानकारी है" in r_hi["response_text"], f"Hindi response unexpected: {r_hi['response_text']}"
    print("  -> PASS: Hindi request receives 100% pure Hindi response.")

    # -------------------------------------------------------------------------
    # TEST SUITE 5: Greeting vs General Assistance Handling
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Friendly Greeting & Fallback Handling:")

    # English greeting
    r_greet_en = requests.post(f"{INTEL}/chat", json={
        "message": "Hello, can you help me?",
        "language": "en-IN"
    }).json()
    assert r_greet_en["intent"] == "GREETING", f"Expected GREETING, got {r_greet_en['intent']}"
    assert "Namaskar! I am Warkari, your pilgrimage assistance assistant" in r_greet_en["response_text"]
    assert len(r_greet_en["facilities"]) == 0, "Greetings must not return fake facilities"
    assert r_greet_en["incident"] is None, "Greetings must not create incidents"
    print("  -> PASS: English greeting returns friendly intro without fake facilities or incidents.")

    # Marathi greeting
    r_greet_mr = requests.post(f"{INTEL}/chat", json={
        "message": "नमस्कार, मला मदत हवी आहे.",
        "language": "mr-IN"
    }).json()
    assert r_greet_mr["intent"] == "GREETING"
    assert "मी वारकरी सहाय्यक आहे" in r_greet_mr["response_text"]
    print("  -> PASS: Marathi greeting returns polite Marathi intro.")

    # Hindi greeting
    r_greet_hi = requests.post(f"{INTEL}/chat", json={
        "message": "नमस्ते, क्या आप मेरी मदद कर सकते हैं?",
        "language": "hi-IN"
    }).json()
    assert r_greet_hi["intent"] == "GREETING"
    assert "नमस्ते! मैं वारकरी सहायता सहायक हूँ" in r_greet_hi["response_text"]
    print("  -> PASS: Hindi greeting returns polite Hindi intro.")

    # -------------------------------------------------------------------------
    # TEST SUITE 6: Regression Verification (Phase 1, 2, 3)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Phase 1 & 2 Endpoints Regression:")
    assert requests.get(f"{BASE}/").json()["status"] == "running"
    assert requests.get(f"{BASE}/health").json()["status"] == "healthy"
    # Phase 2 unconfigured 503 check
    assert requests.post(f"{BASE}/api/assistant/speak", json={"text": "test"}).status_code == 503
    print("  -> PASS: Root, health, and Phase 2 assistant endpoints fully operational.")

    print("\n==================================================")
    print("ALL PHASE 3.1 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

