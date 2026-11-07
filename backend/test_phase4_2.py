"""Comprehensive Isolated Integration and Unit Test Suite for Phase 4.2 Auth & RBAC."""

import os
import unittest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db, Base
from backend.models import User, VolunteerProfile, UserSession, AuditLog
from backend.migrations.migrate_phase4_1 import run_migration
from backend.utils.security import hash_password, create_access_token

TEST_DB = "test_phase4_2_isolated.db"


class TestPhase42AuthAndRBAC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        # Initialize fresh isolated test database with all models & migrations
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

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_01_pilgrim_registration_success(self):
        """1. Test pilgrim registration."""
        res = self.client.post("/api/v1/auth/register", json={
            "name": "Tukaram Maharaj",
            "phone": "+919800000001",
            "password": "Password123!",
            "requested_role": "pilgrim"
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Tukaram Maharaj")
        self.assertEqual(data["role"], "pilgrim")
        self.assertIsNone(data["volunteer_status"])

    def test_02_volunteer_registration_creates_pending_profile(self):
        """2. Test volunteer registration creates VolunteerProfile in PENDING status."""
        res = self.client.post("/api/v1/auth/register", json={
            "name": "Namdev Sevak",
            "phone": "+919800000002",
            "password": "Password123!",
            "requested_role": "volunteer",
            "sector": "Wakhari Camp",
            "skills": '["crowd_control"]'
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["role"], "volunteer")
        self.assertEqual(data["volunteer_status"], "PENDING")
        self.assertEqual(data["volunteer_sector"], "Wakhari Camp")

    def test_03_rejection_of_coordinator_and_admin_self_registration(self):
        """3. Test rejection of coordinator/admin public registration."""
        res1 = self.client.post("/api/v1/auth/register", json={
            "name": "Fake Coordinator",
            "phone": "+919800000003",
            "password": "Password123!",
            "requested_role": "coordinator"
        })
        self.assertEqual(res1.status_code, 400)
        self.assertIn("Privileged roles", res1.json()["detail"])

        res2 = self.client.post("/api/v1/auth/register", json={
            "name": "Fake Admin",
            "phone": "+919800000004",
            "password": "Password123!",
            "requested_role": "admin"
        })
        self.assertEqual(res2.status_code, 400)

    def test_04_successful_login_and_token_issuance(self):
        """4. Test successful login returning access_token and refresh cookie."""
        res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertIn("refresh_token", res.cookies)

    def test_05_incorrect_password(self):
        """5. Test incorrect password returns generic 401."""
        res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "WrongPassword!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "Invalid phone number or password.")

    def test_06_account_lockout_after_failed_attempts(self):
        """6. Test account lockout after 5 consecutive failures."""
        phone = "+919800000099"
        self.client.post("/api/v1/auth/register", json={
            "name": "Lockout User",
            "phone": phone,
            "password": "Password123!"
        })
        for _ in range(4):
            r = self.client.post("/api/v1/auth/login", json={"phone": phone, "password": "WrongPassword"})
            self.assertEqual(r.status_code, 401)

        # 5th attempt triggers lockout
        r5 = self.client.post("/api/v1/auth/login", json={"phone": phone, "password": "WrongPassword"})
        self.assertEqual(r5.status_code, 403)
        self.assertIn("Account locked", r5.json()["detail"])

    def test_07_access_token_validation_and_get_me(self):
        """7. Test authenticated GET /api/v1/auth/me."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]
        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["name"], "Tukaram Maharaj")

    def test_08_refresh_token_rotation(self):
        """8. Test refresh-token rotation (RTR)."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "Password123!"
        })
        raw_refresh_1 = login_res.json()["refresh_token"]

        ref_res = self.client.post("/api/v1/auth/refresh", json={"refresh_token": raw_refresh_1})
        self.assertEqual(ref_res.status_code, 200)
        raw_refresh_2 = ref_res.json()["refresh_token"]
        self.assertNotEqual(raw_refresh_1, raw_refresh_2)

    def test_09_refresh_token_reuse_detection(self):
        """9. Test refresh-token reuse triggers session termination."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "Password123!"
        })
        raw_refresh_1 = login_res.json()["refresh_token"]

        # First refresh succeeds
        ref1 = self.client.post("/api/v1/auth/refresh", json={"refresh_token": raw_refresh_1})
        self.assertEqual(ref1.status_code, 200)

        # Re-presenting old token (REUSE DETECTED!)
        ref2 = self.client.post("/api/v1/auth/refresh", json={"refresh_token": raw_refresh_1})
        self.assertEqual(ref2.status_code, 401)
        self.assertIn("Token reuse detected", ref2.json()["detail"])

    def test_10_logout_and_session_revocation(self):
        """10. Test logout revokes refresh session."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000002",
            "password": "Password123!"
        })
        raw_refresh = login_res.json()["refresh_token"]

        logout_res = self.client.post("/api/v1/auth/logout", json={"refresh_token": raw_refresh})
        self.assertEqual(logout_res.status_code, 200)

        # Trying to use revoked refresh token fails
        post_logout = self.client.post("/api/v1/auth/refresh", json={"refresh_token": raw_refresh})
        self.assertEqual(post_logout.status_code, 401)

    def test_11_unauthorized_admin_access_rejected(self):
        """11. Test non-admin user cannot approve volunteers."""
        login_res = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000001",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]

        res = self.client.put("/api/v1/auth/volunteers/1/approve", 
                              headers={"Authorization": f"Bearer {token}"},
                              json={"approval_status": "APPROVED"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied. Required role: admin", res.json()["detail"])

    def test_12_admin_volunteer_approval_and_role_escalation(self):
        """12. Test administrator can approve volunteer and update role."""
        db = self.TestingSessionLocal()
        admin = User(
            name="Admin Head",
            phone="+919800000999",
            hashed_password=hash_password("AdminPass123!"),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
        db.close()

        # Login as admin
        admin_login = self.client.post("/api/v1/auth/login", json={
            "phone": "+919800000999",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]

        # Approve volunteer profile #1
        app_res = self.client.put("/api/v1/auth/volunteers/1/approve",
                                 headers={"Authorization": f"Bearer {admin_token}"},
                                 json={"approval_status": "APPROVED", "sector": "Wakhari North"})
        self.assertEqual(app_res.status_code, 200)

        # Update pilgrim #1 to coordinator
        role_res = self.client.put("/api/v1/auth/users/1/role",
                                   headers={"Authorization": f"Bearer {admin_token}"},
                                   json={"role": "coordinator"})
        self.assertEqual(role_res.status_code, 200)

        # Verify role updated in DB
        db2 = self.TestingSessionLocal()
        updated_user = db2.query(User).filter(User.id == 1).first()
        self.assertEqual(updated_user.role, "coordinator")
        db2.close()

    def test_13_foreign_key_integrity(self):
        """13. PRAGMA foreign_key_check on isolated test DB."""
        from sqlalchemy import text
        db = self.TestingSessionLocal()
        fks = db.execute(text("PRAGMA foreign_key_check;")).fetchall()
        self.assertEqual(len(fks), 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
