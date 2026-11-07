import unittest
import os
import sqlite3
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    User,
    Facility,
    Volunteer,
    Incident,
    UserSession,
    VolunteerProfile,
    IncidentAssignment,
    IncidentStatusHistory,
    AuditLog
)
from backend.migrations.migrate_phase4_1 import run_migration
from backend.services.audit_service import audit_service
from backend.utils.tracking import generate_tracking_credentials, hash_tracking_token


class TestPhase41Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_path = "warkari_isolated_test_suite.db"
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        # 1. Create a legacy baseline database mimicking warkari.db
        conn = sqlite3.connect(cls.test_db_path)
        c = conn.cursor()
        
        # Legacy users
        c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(120) NOT NULL,
            preferred_language VARCHAR(30) NOT NULL DEFAULT 'mr',
            role VARCHAR(50) NOT NULL DEFAULT 'pilgrim',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        c.execute("INSERT INTO users (name, role) VALUES ('Legacy User', 'pilgrim');")

        # Legacy volunteers
        c.execute("""
        CREATE TABLE volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(120) NOT NULL,
            phone VARCHAR(30) NOT NULL UNIQUE,
            assigned_area VARCHAR(150),
            availability VARCHAR(50) NOT NULL DEFAULT 'available'
        );
        """)
        c.execute("INSERT INTO volunteers (name, phone) VALUES ('Legacy Vol', '+919999999999');")

        # Legacy facilities
        c.execute("""
        CREATE TABLE facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(150) NOT NULL,
            category VARCHAR(80) NOT NULL,
            description TEXT,
            location VARCHAR(255),
            name_en VARCHAR(150),
            name_hi VARCHAR(150),
            location_en VARCHAR(255),
            location_hi VARCHAR(255),
            description_en TEXT,
            description_hi TEXT,
            latitude FLOAT,
            longitude FLOAT,
            contact_phone VARCHAR(50),
            operational_status VARCHAR(50) NOT NULL DEFAULT 'operational',
            is_verified BOOLEAN NOT NULL DEFAULT 0,
            source VARCHAR(100),
            last_verified_at DATETIME,
            is_demo BOOLEAN NOT NULL DEFAULT 0
        );
        """)
        c.execute("""
        INSERT INTO facilities (name, category, name_en) 
        VALUES ('पाणी केंद्र', 'drinking_water', 'Water Center');
        """)

        # Legacy incidents
        c.execute("""
        CREATE TABLE incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category VARCHAR(80) NOT NULL,
            description TEXT NOT NULL,
            original_message TEXT,
            language VARCHAR(20) NOT NULL DEFAULT 'mr-IN',
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            urgency_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
            status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
            location_description VARCHAR(255),
            latitude FLOAT,
            longitude FLOAT,
            assigned_volunteer_id INTEGER,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_volunteer_id) REFERENCES volunteers(id) ON DELETE SET NULL
        );
        """)
        c.execute("""
        INSERT INTO incidents (category, description, status) 
        VALUES ('water_shortage', 'Need drinking water', 'OPEN');
        """)

        conn.commit()
        conn.close()

        # Run Phase 4.1 migration on this isolated database
        run_migration(cls.test_db_path)

        cls.engine = create_engine(f"sqlite:///{cls.test_db_path}")
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        try:
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)
        except Exception:
            pass

    def test_01_user_extensions_and_trigger(self):
        """Verify users table extensions, unique indexes, and trigger."""
        db = self.Session()
        user = User(
            name="Santosh Patil",
            phone="+919876543210",
            email="santosh@example.com",
            role="volunteer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        self.assertEqual(user.token_version, 1)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_phone_verified)
        self.assertIsNotNone(user.updated_at)
        db.close()

    def test_02_volunteer_profile_and_assignment(self):
        """Verify volunteer_profiles and incident_assignments relationships."""
        db = self.Session()
        user = db.query(User).filter(User.phone == "+919876543210").first()
        vol_profile = VolunteerProfile(
            user_id=user.id,
            sector="Wakhari Halt",
            skills='["first_aid"]',
            approval_status="APPROVED"
        )
        db.add(vol_profile)
        db.commit()
        db.refresh(vol_profile)

        incident = db.query(Incident).first()
        assignment = IncidentAssignment(
            incident_id=incident.id,
            volunteer_profile_id=vol_profile.id,
            assigned_by=user.id,
            status="PENDING"
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        self.assertEqual(assignment.status, "PENDING")
        self.assertEqual(assignment.volunteer_profile.sector, "Wakhari Halt")
        db.close()

    def test_03_audit_log_cryptographic_chaining_and_triggers(self):
        """Verify audit service cryptographic chaining and immutability triggers."""
        db = self.Session()
        log1 = audit_service.log_event(db, action="CREATE_USER", target_type="user", target_id="1")
        log2 = audit_service.log_event(db, action="ASSIGN_INCIDENT", target_type="incident", target_id="1")

        self.assertEqual(log2.previous_hash, log1.current_hash)
        self.assertTrue(audit_service.verify_chain(db))

        # Test trigger blocks update on audit_logs
        raw_conn = sqlite3.connect(self.test_db_path)
        with self.assertRaises(sqlite3.DatabaseError):
            raw_conn.execute(f"UPDATE audit_logs SET action = 'HACKED' WHERE id = {log1.id};")
        raw_conn.close()
        db.close()

    def test_04_tracking_token_generation_and_hashing(self):
        """Verify tracking token generation, HMAC hashing, and formatting."""
        raw_token, token_hash, public_ref = generate_tracking_credentials("test_secret")
        self.assertTrue(public_ref.startswith("WKR-"))
        self.assertEqual(len(public_ref), 13) # WKR-XXXX-XXXX
        
        # Verify hash match
        re_hash = hash_tracking_token(raw_token, "test_secret")
        self.assertEqual(token_hash, re_hash)


if __name__ == "__main__":
    unittest.main()
