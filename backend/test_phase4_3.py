"""Comprehensive Isolated Test Suite for Phase 4.3 Incident Management, Assignment & Public Tracking."""

import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db, Base
from backend.models import User, VolunteerProfile, Incident, IncidentAssignment
from backend.migrations.migrate_phase4_1 import run_migration
from backend.utils.security import hash_password, create_access_token
from backend.services.incident_service import incident_service

TEST_DB = "test_phase4_3_isolated.db"


class TestPhase43Workflow(unittest.TestCase):
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

        # Seed roles for testing in isolated DB
        db = cls.TestingSessionLocal()
        admin = User(name="Head Admin", phone="+919811111111", hashed_password=hash_password("Pass123!"), role="admin")
        coordinator = User(name="Zone Coordinator", phone="+919822222222", hashed_password=hash_password("Pass123!"), role="coordinator")
        volunteer_user = User(name="Field Sevak 1", phone="+919833333333", hashed_password=hash_password("Pass123!"), role="volunteer")
        volunteer_user_2 = User(name="Field Sevak 2", phone="+919844444444", hashed_password=hash_password("Pass123!"), role="volunteer")
        unapproved_vol_user = User(name="Pending Sevak", phone="+919855555555", hashed_password=hash_password("Pass123!"), role="volunteer")
        pilgrim_user = User(name="Pilgrim Vitthal", phone="+919866666666", hashed_password=hash_password("Pass123!"), role="pilgrim")

        db.add_all([admin, coordinator, volunteer_user, volunteer_user_2, unapproved_vol_user, pilgrim_user])
        db.commit()

        # Volunteer Profiles
        vol_profile_1 = VolunteerProfile(user_id=volunteer_user.id, sector="Wakhari", approval_status="APPROVED")
        vol_profile_2 = VolunteerProfile(user_id=volunteer_user_2.id, sector="Pandharpur", approval_status="APPROVED")
        unapproved_profile = VolunteerProfile(user_id=unapproved_vol_user.id, sector="Mohol", approval_status="PENDING")

        db.add_all([vol_profile_1, vol_profile_2, unapproved_profile])
        db.commit()

        cls.vol_profile_1_id = vol_profile_1.id
        cls.vol_profile_2_id = vol_profile_2.id
        cls.unapproved_profile_id = unapproved_profile.id

        cls.coord_token = create_access_token(coordinator.id, coordinator.role, 1)
        cls.vol_token_1 = create_access_token(volunteer_user.id, volunteer_user.role, 1)
        cls.vol_token_2 = create_access_token(volunteer_user_2.id, volunteer_user_2.role, 1)
        cls.pilgrim_token = create_access_token(pilgrim_user.id, pilgrim_user.role, 1)
        db.close()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_01_incident_creation_and_tracking_token(self):
        """1 & 2. Test incident creation, public reference format, and token generation."""
        res = self.client.post("/api/intelligence/incidents", json={
            "category": "water_shortage",
            "description": "Drinking water tanker needed at camp gate",
            "language": "en-IN",
            "urgency_level": "HIGH"
        })
        self.assertIn(res.status_code, [200, 201])
        data = res.json()
        self.assertIn("public_reference", data)
        self.assertTrue(data["public_reference"].startswith("WKR-"))
        self.assertIn("raw_tracking_token", data)
        self.assertIsNotNone(data["raw_tracking_token"])
        TestPhase43Workflow.created_token = data["raw_tracking_token"]
        TestPhase43Workflow.created_ref = data["public_reference"]
        TestPhase43Workflow.created_incident_id = data["id"]

    def test_02_public_tracking_with_valid_token(self):
        """3, 4, 5 & 6. Test POST /api/v1/public/incidents/track."""
        res = self.client.post("/api/v1/public/incidents/track", json={
            "token": TestPhase43Workflow.created_token
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["public_reference"], TestPhase43Workflow.created_ref)
        self.assertEqual(data["category"], "water_shortage")
        self.assertEqual(data["status"], "OPEN")
        self.assertIn("status_message", data)
        
        # Invariant checks: No PII, no internal sequential integer ID, no raw token
        self.assertNotIn("id", data)
        self.assertNotIn("ticket_id", data)
        self.assertNotIn("token", data)
        self.assertNotIn("phone", data)

        # Test invalid token returns 404
        bad_res = self.client.post("/api/v1/public/incidents/track", json={
            "token": "wkr_invalid_token_1234567890abcdefghijklmnop"
        })
        self.assertEqual(bad_res.status_code, 404)

    def test_03_coordinator_assignment_authorization(self):
        """7, 8, 9 & 17. Test coordinator assignment, unapproved rejection, pilgrim rejection, and conflict prevention."""
        # Pilgrim cannot assign
        p_res = self.client.post(f"/api/v1/coordinator/incidents/{TestPhase43Workflow.created_incident_id}/assign",
                                 headers={"Authorization": f"Bearer {self.pilgrim_token}"},
                                 json={"volunteer_profile_id": self.vol_profile_1_id})
        self.assertEqual(p_res.status_code, 403)

        # Coordinator cannot assign UNAPPROVED volunteer
        u_res = self.client.post(f"/api/v1/coordinator/incidents/{TestPhase43Workflow.created_incident_id}/assign",
                                 headers={"Authorization": f"Bearer {self.coord_token}"},
                                 json={"volunteer_profile_id": self.unapproved_profile_id})
        self.assertEqual(u_res.status_code, 400)
        self.assertIn("Volunteer is not approved", u_res.json()["detail"])

        # Coordinator successfully assigns APPROVED volunteer
        c_res = self.client.post(f"/api/v1/coordinator/incidents/{TestPhase43Workflow.created_incident_id}/assign",
                                 headers={"Authorization": f"Bearer {self.coord_token}"},
                                 json={"volunteer_profile_id": self.vol_profile_1_id})
        self.assertEqual(c_res.status_code, 200)
        assign_data = c_res.json()
        self.assertEqual(assign_data["status"], "PENDING")
        TestPhase43Workflow.assignment_id = assign_data["id"]

        # Conflict prevention: cannot double assign active/pending ticket
        conf_res = self.client.post(f"/api/v1/coordinator/incidents/{TestPhase43Workflow.created_incident_id}/assign",
                                    headers={"Authorization": f"Bearer {self.coord_token}"},
                                    json={"volunteer_profile_id": self.vol_profile_2_id})
        self.assertEqual(conf_res.status_code, 409)

    def test_04_volunteer_acceptance_and_lifecycle_flow(self):
        """10, 11, 13, 14, 15 & 16. Test volunteer acceptance, cross-volunteer prevention, and state machine."""
        # Volunteer 2 cannot accept Volunteer 1's assignment
        v2_res = self.client.post(f"/api/v1/volunteer/assignments/{TestPhase43Workflow.assignment_id}/accept",
                                  headers={"Authorization": f"Bearer {self.vol_token_2}"})
        self.assertEqual(v2_res.status_code, 403)

        # Volunteer 1 accepts
        v1_res = self.client.post(f"/api/v1/volunteer/assignments/{TestPhase43Workflow.assignment_id}/accept",
                                  headers={"Authorization": f"Bearer {self.vol_token_1}"})
        self.assertEqual(v1_res.status_code, 200)
        self.assertEqual(v1_res.json()["status"], "ACCEPTED")

        # Invalid transition: Cannot jump straight to RESOLVED from ACKNOWLEDGED
        bad_trans = self.client.post(f"/api/v1/volunteer/incidents/{TestPhase43Workflow.created_incident_id}/resolve",
                                     headers={"Authorization": f"Bearer {self.vol_token_1}"})
        self.assertEqual(bad_trans.status_code, 400)

        # Legitimate progress: EN_ROUTE -> ON_SCENE -> RESOLVED
        en_route_res = self.client.post(f"/api/v1/volunteer/incidents/{TestPhase43Workflow.created_incident_id}/en-route",
                                        headers={"Authorization": f"Bearer {self.vol_token_1}"},
                                        json={"notes": "Traveling by vehicle"})
        self.assertEqual(en_route_res.status_code, 200)

        on_scene_res = self.client.post(f"/api/v1/volunteer/incidents/{TestPhase43Workflow.created_incident_id}/on-scene",
                                        headers={"Authorization": f"Bearer {self.vol_token_1}"},
                                        json={"notes": "Arrived at camp gate"})
        self.assertEqual(on_scene_res.status_code, 200)

        resolve_res = self.client.post(f"/api/v1/volunteer/incidents/{TestPhase43Workflow.created_incident_id}/resolve",
                                       headers={"Authorization": f"Bearer {self.vol_token_1}"},
                                       json={"notes": "Water tanker distributed"})
        self.assertEqual(resolve_res.status_code, 200)
        self.assertEqual(resolve_res.json()["status"], "RESOLVED")

    def test_05_rejection_workflow(self):
        """12. Test rejection workflow frees incident for re-triage."""
        db = self.TestingSessionLocal()
        inc = incident_service.create_incident(db, "sanitation_issue", "Mobile toilet clogged")
        db.close()

        # Coordinator assigns volunteer 1
        c_res = self.client.post(f"/api/v1/coordinator/incidents/{inc.id}/assign",
                                 headers={"Authorization": f"Bearer {self.coord_token}"},
                                 json={"volunteer_profile_id": self.vol_profile_1_id})
        assign_id = c_res.json()["id"]

        # Volunteer rejects with reason
        rej_res = self.client.post(f"/api/v1/volunteer/assignments/{assign_id}/reject",
                                   headers={"Authorization": f"Bearer {self.vol_token_1}"},
                                   json={"reason": "Attending urgent medical triage elsewhere"})
        self.assertEqual(rej_res.status_code, 200)
        self.assertEqual(rej_res.json()["status"], "REJECTED")

        # Verify incident status reverted to TRIAGED
        db2 = self.TestingSessionLocal()
        refreshed_inc = db2.query(Incident).filter(Incident.id == inc.id).first()
        self.assertEqual(refreshed_inc.status, "TRIAGED")
        self.assertIsNone(refreshed_inc.assigned_volunteer_id)
        db2.close()


if __name__ == "__main__":
    unittest.main()
