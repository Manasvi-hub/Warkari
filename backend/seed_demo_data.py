"""Seed test script for explicitly labelled synthetic demo facilities.

IMPORTANT:
Every record created by this script is explicitly marked with `is_demo=True`.
Demo data can NEVER be marked as `is_verified=True` and must never include
fake or placeholder phone numbers/emergency contacts.
"""

import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Facility


DEMO_FACILITIES = [
    {
        "name": "सार्वजनिक पिण्याचे पाणी केंद्र",
        "category": "drinking_water",
        "description": "स्वच्छ पिण्याच्या पाण्याचा टँकर व फिल्टर पाण्याची सोय",
        "location": "वाखरी मुक्काम तळ ",
        "latitude": 17.6833,
        "longitude": 75.3167,
        "contact_phone": None,
        "operational_status": "operational",
        "is_verified": False,
        "is_demo": True,
        "source": "demo_test_data",
        "last_verified_at": None,
    },
    {
        "name": "आरोग्य शिबिर व प्रथमोपचार केंद्र",
        "category": "medical",
        "description": "प्राथमिक उपचार, ओआरएस, ताप व वेदनाशामक औषधे मोफत उपलब्ध ",
        "location": "पंढरपूर प्रवेशद्वार, मोहोळ रस्ता ",
        "latitude": 17.6780,
        "longitude": 75.3250,
        "contact_phone": None,
        "operational_status": "operational",
        "is_verified": False,
        "is_demo": True,
        "source": "demo_test_data",
        "last_verified_at": None,
    },
    {
        "name": "सार्वजनिक स्वच्छतागृह व फिरती शौचालये ",
        "category": "sanitation",
        "description": "स्त्री व पुरुषांसाठी स्वतंत्र फिरते शौचालय ",
        "location": "चंद्रभागा वाळवंट घाट परिसर ",
        "latitude": 17.6740,
        "longitude": 75.3310,
        "contact_phone": None,
        "operational_status": "operational",
        "is_verified": False,
        "is_demo": True,
        "source": "demo_test_data",
        "last_verified_at": None,
    },
    {
        "name": "वारकरी अन्नछत्र सेवा ",
        "category": "food",
        "description": "महाप्रसाद आणि पिण्याचे पाणी वाटप ",
        "location": "स्टेशन रोड, पंढरपूर ",
        "latitude": 17.6765,
        "longitude": 75.3280,
        "contact_phone": None,
        "operational_status": "operational",
        "is_verified": False,
        "is_demo": True,
        "source": "demo_test_data",
        "last_verified_at": None,
    },
    {
        "name": "विश्रांती मंडप व निवारा तंबू ",
        "category": "resting_area",
        "description": "वारकऱ्यांसाठी सावली, पिण्याचे पाणी व विश्रांती कक्ष ",
        "location": "भोसले क्रीडा संकुल परिसर ",
        "latitude": 17.6810,
        "longitude": 75.3200,
        "contact_phone": None,
        "operational_status": "operational",
        "is_verified": False,
        "is_demo": True,
        "source": "demo_test_data",
        "last_verified_at": None,
    },
]


def seed_demo_data():
    db: Session = SessionLocal()
    try:
        count = db.query(Facility).filter(Facility.is_demo == True).count()
        if count == 0:
            for item in DEMO_FACILITIES:
                fac = Facility(**item)
                db.add(fac)
            db.commit()
            print(f"Seeded {len(DEMO_FACILITIES)} explicitly marked demo facilities.")
        else:
            print(f"Database already contains {count} demo facilities. Skipping re-seed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
