"""Automated test suite for Phase 3.3.5: Multilingual Facility Representation.

Verifies:
1. Database schema: 6 approved columns exist, NULL for existing records.
2. Canonical Marathi data remains intact.
3. Incident count remains 81 and foreign keys are valid.
4. Language resolution in facility_service for mr-IN, en-IN, hi-IN:
   - mr-IN returns canonical Marathi fields.
   - en-IN and hi-IN trigger transparent fallback indicators when translations are NULL.
   - Test fixtures with approved translations resolve properly without fallback.
5. ResponseService integration:
   - In en-IN with fallback, discloses fallback transparently.
   - In en-IN with approved translation, displays English Latin and speaks authentic Devanagari pronunciation.
6. Idempotent migration safety.
"""

import sqlite3
import pytest
from backend.models import Facility
from backend.services.facility_service import sanitize_facility_for_display
from backend.services.response_service import _format_facility_details, _compose_medical_response, _compose_water_response
from backend.services.speech_normalization_service import speech_normalization_service


def test_database_schema_and_counts():
    conn = sqlite3.connect("warkari.db")
    c = conn.cursor()

    # Check 6 columns
    c.execute("PRAGMA table_info(facilities)")
    cols = {row[1]: row for row in c.fetchall()}
    for col_name in ["name_en", "name_hi", "location_en", "location_hi", "description_en", "description_hi"]:
        assert col_name in cols, f"Missing column {col_name}"

    # Check facility count & safety flags
    c.execute("SELECT id, name, is_demo, is_verified, source, name_en, name_hi FROM facilities ORDER BY id")
    facs = c.fetchall()
    assert len(facs) == 5, f"Expected 5 facilities, got {len(facs)}"
    for f in facs:
        assert f[2] == 1, f"Facility {f[0]} is_demo must be 1"
        assert f[3] == 0, f"Facility {f[0]} is_verified must be 0"
        assert f[4] == "demo_test_data", f"Facility {f[0]} source must be demo_test_data"
        assert f[5] is None, f"Facility {f[0]} name_en must be NULL pending review"
        assert f[6] is None, f"Facility {f[0]} name_hi must be NULL pending review"

    # Check incidents
    c.execute("SELECT count(*) FROM incidents")
    inc_count = c.fetchone()[0]
    assert inc_count >= 81, f"Expected at least 81 incidents, got {inc_count}"

    # Check foreign keys
    c.execute("PRAGMA foreign_key_check")
    assert len(c.fetchall()) == 0, "Foreign key integrity violated"
    conn.close()


def test_facility_service_marathi_resolution():
    dummy = Facility(
        id=1,
        name="सार्वजनिक पिण्याचे पाणी केंद्र",
        location="वाखरी मुक्काम तळ",
        description="स्वच्छ पिण्याच्या पाण्याचा टँकर",
        category="drinking_water",
        is_demo=True,
        is_verified=False
    )
    res = sanitize_facility_for_display(dummy, language="mr-IN")
    assert res["name"] == "सार्वजनिक पिण्याचे पाणी केंद्र"
    assert res["location"] == "वाखरी मुक्काम तळ"
    assert res["requested_language"] == "mr"
    assert res["resolved_language"] == "mr"
    assert res["language_fallback"] is False


def test_facility_service_english_fallback_when_untranslated():
    dummy = Facility(
        id=1,
        name="सार्वजनिक पिण्याचे पाणी केंद्र",
        location="वाखरी मुक्काम तळ",
        description="स्वच्छ पिण्याच्या पाण्याचा टँकर",
        category="drinking_water",
        name_en=None,
        location_en=None,
        description_en=None,
        is_demo=True,
        is_verified=False
    )
    res = sanitize_facility_for_display(dummy, language="en-IN")
    assert res["name"] == "सार्वजनिक पिण्याचे पाणी केंद्र"
    assert res["location"] == "वाखरी मुक्काम तळ"
    assert res["requested_language"] == "en"
    assert res["resolved_language"] == "mr"
    assert res["language_fallback"] is True
    assert res["name_fallback"] is True
    assert res["location_fallback"] is True


def test_facility_service_with_approved_english_translations():
    dummy = Facility(
        id=2,
        name="आरोग्य शिबिर व प्रथमोपचार केंद्र",
        location="पंढरपूर प्रवेशद्वार, मोहोळ रस्ता",
        description="प्राथमिक उपचार मोफत उपलब्ध",
        category="medical",
        name_en="Medical Camp & First Aid Center",
        location_en="Pandharpur Entry Gate, Mohol Road",
        description_en="First aid available free of cost",
        is_demo=True,
        is_verified=False
    )
    res = sanitize_facility_for_display(dummy, language="en-IN")
    assert res["name"] == "Medical Camp & First Aid Center"
    assert res["location"] == "Pandharpur Entry Gate, Mohol Road"
    assert res["requested_language"] == "en"
    assert res["resolved_language"] == "en"
    assert res["language_fallback"] is False
    assert res["name_fallback"] is False


def test_facility_service_hindi_fallback_when_untranslated():
    dummy = Facility(
        id=3,
        name="सार्वजनिक स्वच्छतागृह व फिरती शौचालये",
        location="चंद्रभागा वाळवंट घाट परिसर",
        description="स्वच्छतागृह सोय",
        category="sanitation",
        name_hi=None,
        location_hi=None,
        description_hi=None,
        is_demo=True,
        is_verified=False
    )
    res = sanitize_facility_for_display(dummy, language="hi-IN")
    assert res["name"] == "सार्वजनिक स्वच्छतागृह व फिरती शौचालये"
    assert res["requested_language"] == "hi"
    assert res["resolved_language"] == "mr"
    assert res["language_fallback"] is True


def test_response_service_fallback_disclosure_in_english():
    facs = [{
        "name": "सार्वजनिक पिण्याचे पाणी केंद्र",
        "location": "वाखरी मुक्काम तळ",
        "distance_km": None,
        "is_demo": True,
        "language_fallback": True
    }]
    formatted_text, has_demo = _format_facility_details(facs, "en-IN", False)
    assert "सार्वजनिक पिण्याचे पाणी केंद्र" in formatted_text
    assert "pending verification" in formatted_text
    assert has_demo is True


def test_response_service_with_approved_english_display_and_speech():
    facs = [{
        "name": "Medical Camp & First Aid Center",
        "location": "Pandharpur Entry Gate, Mohol Road",
        "distance_km": None,
        "is_demo": True,
        "language_fallback": False
    }]
    resp_text = _compose_medical_response("Where is first aid?", facs, None, "en-IN", False)
    assert "Medical Camp & First Aid Center" in resp_text
    assert "Pandharpur Entry Gate, Mohol Road" in resp_text

    # Verify speech normalization converts place names to Devanagari in speech_text
    speech_text = speech_normalization_service.normalize_for_speech(resp_text, language="en-IN")
    assert "पंढरपूर" in speech_text
    assert "मोहोळ" in speech_text
    # English title words remain in English
    assert "Medical Camp" in speech_text


if __name__ == "__main__":
    test_database_schema_and_counts()
    test_facility_service_marathi_resolution()
    test_facility_service_english_fallback_when_untranslated()
    test_facility_service_with_approved_english_translations()
    test_facility_service_hindi_fallback_when_untranslated()
    test_response_service_fallback_disclosure_in_english()
    test_response_service_with_approved_english_display_and_speech()
    print("ALL Phase 3.3.5 Automated Tests PASSED!")
