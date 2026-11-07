"""End-to-End Integration Test Suite for Phase 5.
Validates the complete Pilgrim -> Assistant -> Coordinator -> Volunteer -> Public Tracking journey,
facility retrieval across languages, and emergency guidance safeguards on an isolated test DB.
"""

import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db, Base
from backend.models import User, VolunteerProfile, Incident, Facility
from backend.migrations.migrate_phase4_1 import run_migration
from backend.utils.security import hash_password, create_access_token

TEST_DB = "test_phase5_e2e_isolated.db"


class TestPhase5EndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        cls.engine = create_engine(f"sqlite:///{TEST_DB}", connect_args={"check_same_thread": False})
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)
        run_migration(TEST_DB)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Seed initial coordinator, volunteer, facilities in isolated DB
        db = cls.TestingSessionLocal()
        coord_user = User(
            name="Zone Coordinator",
            phone="+919800000001",
            email="coordinator@warkari.org",
            hashed_password=hash_password("CoordPass123!"),
            role="coordinator"
        )
        vol_user = User(
            name="Field Volunteer Santosh",
            phone="+919800000002",
            email="santosh@warkari.org",
            hashed_password=hash_password("VolPass123!"),
            role="volunteer"
        )
        db.add_all([coord_user, vol_user])
        db.commit()

        vol_profile = VolunteerProfile(
            user_id=vol_user.id,
            sector="Wakhari",
            approval_status="APPROVED",
            availability="available"
        )
        db.add(vol_profile)

        # Seed facilities (canonical Marathi in `name`, English in `name_en`, Hindi in `name_hi`)
        fac1 = Facility(
            name="वाखारी पिण्याचे पाणी केंद्र",
            name_en="Wakhari Water Point",
            name_hi="वाखारी पेयजल केंद्र",
            category="drinking_water",
            latitude=17.6833,
            longitude=75.3167,
            location="Near Wakhari Toll, Pandharpur Road",
            is_verified=True,
            operational_status="operational"
        )
        fac2 = Facility(
            name="पंढरपूर वैद्यकीय मदत केंद्र",
            name_en="Pandharpur Aid Station",
            name_hi="पंढरपुर चिकित्सा सहायता केंद्र",
            category="medical",
            latitude=17.6780,
            longitude=75.3250,
            location="Pandharpur Entrance",
            is_verified=True,
            operational_status="operational"
        )
        db.add_all([fac1, fac2])
        db.commit()

        cls.coord_user_id = coord_user.id
        cls.vol_user_id = vol_user.id
        cls.vol_profile_id = vol_profile.id
        db.close()

        cls.coord_token = create_access_token(cls.coord_user_id, "coordinator", 1)
        cls.vol_token = create_access_token(cls.vol_user_id, "volunteer", 1)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except OSError:
                pass

    def test_01_pilgrim_registration(self):
        """Step 1: Pilgrim registers an account and logs in."""
        resp = self.client.post("/api/v1/auth/register", json={
            "phone": "+919899999999",
            "name": "Vitthal Pilgrim",
            "password": "PilgrimPass123!",
            "intent": "pilgrim"
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["role"], "pilgrim")

        # Login to obtain token
        login_resp = self.client.post("/api/v1/auth/login", json={
            "phone": "+919899999999",
            "password": "PilgrimPass123!"
        })
        self.assertEqual(login_resp.status_code, 200)
        login_data = login_resp.json()
        self.assertIn("access_token", login_data)

    def test_02_pilgrim_creates_incident_and_gets_token(self):
        """Step 2 & 3: Pilgrim submits assistance request, receives reference and token once."""
        resp = self.client.post("/api/intelligence/incidents", json={
            "category": "medical_emergency",
            "description": "Elderly pilgrim feeling dizzy near Wakhari water point",
            "urgency_level": "MEDIUM",
            "language": "mr-IN",
            "location_description": "Wakhari camp"
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()

        self.assertIn("id", data)
        self.assertIn("public_reference", data)
        self.assertTrue(data["public_reference"].startswith("WKR-"))
        self.assertIn("raw_tracking_token", data)
        self.assertTrue(len(data["raw_tracking_token"]) > 30)

        # Store for downstream tests
        TestPhase5EndToEndIntegration.incident_id = data["id"]
        TestPhase5EndToEndIntegration.public_reference = data["public_reference"]
        TestPhase5EndToEndIntegration.tracking_token = data["raw_tracking_token"]

    def test_03_token_never_returned_on_direct_get(self):
        """Verify token is ephemeral and NEVER exposed on GET /incidents/{id}."""
        inc_id = TestPhase5EndToEndIntegration.incident_id
        resp = self.client.get(f"/api/intelligence/incidents/{inc_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("raw_tracking_token"))

    def test_04_coordinator_lists_and_assigns_incident(self):
        """Step 4 & 5: Coordinator lists open incidents and assigns to approved volunteer."""
        inc_id = TestPhase5EndToEndIntegration.incident_id
        headers = {"Authorization": f"Bearer {self.coord_token}"}

        list_resp = self.client.get("/api/v1/coordinator/incidents", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        page_data = list_resp.json()
        incidents = page_data["items"]
        matching = [i for i in incidents if i["id"] == inc_id]
        self.assertEqual(len(matching), 1)

        assign_resp = self.client.post(
            f"/api/v1/coordinator/incidents/{inc_id}/assign",
            headers=headers,
            json={"volunteer_profile_id": self.vol_profile_id, "notes": "Please assist immediately"}
        )
        self.assertEqual(assign_resp.status_code, 200)
        assign_data = assign_resp.json()
        self.assertEqual(assign_data["status"], "PENDING")
        self.assertEqual(assign_data["volunteer_profile_id"], self.vol_profile_id)
        TestPhase5EndToEndIntegration.assignment_id = assign_data["id"]

    def test_05_volunteer_lifecycle_to_resolution(self):
        """Step 6, 7, 8, 9, 10: Volunteer receives assignment, accepts, moves en-route, on-scene, and resolves."""
        inc_id = TestPhase5EndToEndIntegration.incident_id
        assign_id = TestPhase5EndToEndIntegration.assignment_id
        headers = {"Authorization": f"Bearer {self.vol_token}"}

        # 1. Fetch assignments
        resp = self.client.get("/api/v1/volunteer/assignments", headers=headers)
        self.assertEqual(resp.status_code, 200)
        assignments = resp.json()
        matching = [a for a in assignments if a["incident_id"] == inc_id]
        self.assertEqual(len(matching), 1)

        # 2. Accept assignment
        resp = self.client.post(f"/api/v1/volunteer/assignments/{assign_id}/accept", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ACCEPTED")

        # 3. En route
        resp = self.client.post(f"/api/v1/volunteer/incidents/{inc_id}/en-route", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "EN_ROUTE")

        # 4. On scene
        resp = self.client.post(f"/api/v1/volunteer/incidents/{inc_id}/on-scene", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ON_SCENE")

        # 5. Resolve
        resp = self.client.post(
            f"/api/v1/volunteer/incidents/{inc_id}/resolve",
            headers=headers,
            json={"notes": "First aid administered. Pilgrim resting comfortably."}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "RESOLVED")

    def test_06_public_tracking_verification(self):
        """Step 11: Pilgrim checks status with raw token via public POST endpoint."""
        token = TestPhase5EndToEndIntegration.tracking_token
        ref = TestPhase5EndToEndIntegration.public_reference

        resp = self.client.post("/api/v1/public/incidents/track", json={"token": token})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["public_reference"], ref)
        self.assertEqual(data["status"], "RESOLVED")
        self.assertEqual(data["category"], "medical_emergency")
        self.assertIn("status_message", data)
        self.assertIn("यशस्वीरीत्या पूर्ण", data["status_message"])
        # Ensure no PII or internal IDs leak
        self.assertNotIn("assigned_volunteer_id", data)
        self.assertNotIn("user_id", data)
        self.assertNotIn("phone", data)

    def test_07_emergency_safeguards_and_consent(self):
        """Step 12 & 13: Emergency helpline response & missing person consent gating."""
        # Query ambulance helpline via chat
        resp = self.client.post("/api/intelligence/chat", json={
            "message": "रुग्णवाहिका नंबर काय आहे?",
            "language": "mr-IN"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Should provide 108 emergency guidance in response_text
        self.assertTrue("108" in data["response_text"] or "१०८" in data["response_text"])
        self.assertFalse(data.get("awaiting_missing_person_consent", False))

        # Missing person without consent MUST be gated
        inc_fail = self.client.post("/api/intelligence/incidents", json={
            "category": "lost_person",
            "description": "Child missing near temple",
            "user_consent_granted": False
        })
        self.assertEqual(inc_fail.status_code, 400)
        self.assertIn("consent", inc_fail.json()["detail"].lower())

    def test_08_multilingual_facilities_retrieval(self):
        """Step 14: Multilingual facility retrieval and localization."""
        # Marathi
        mr_resp = self.client.get("/api/intelligence/facilities?category=drinking_water&language=mr-IN")
        self.assertEqual(mr_resp.status_code, 200)
        mr_data = mr_resp.json()
        self.assertTrue(len(mr_data) >= 1)
        self.assertEqual(mr_data[0]["name"], "वाखारी पिण्याचे पाणी केंद्र")

        # English
        en_resp = self.client.get("/api/intelligence/facilities?category=drinking_water&language=en-IN")
        self.assertEqual(en_resp.status_code, 200)
        en_data = en_resp.json()
        self.assertTrue(len(en_data) >= 1)
        self.assertEqual(en_data[0]["name"], "Wakhari Water Point")


if __name__ == "__main__":
    unittest.main()
