"""Database Migration Script for Warkari Phase 4.1.

Additive-only schema updates:
1. Adds authentication and lifecycle columns to `users`.
2. Adds tracking token hash and public reference to `incidents`.
3. Creates `user_sessions`, `volunteer_profiles`, `incident_assignments`,
   `incident_status_history`, and `audit_logs`.
4. Creates unique partial indexes and triggers.
5. Preserves all existing facility and incident records.
"""

import sqlite3
import sys
import logging

logger = logging.getLogger("warkari.migration_phase4_1")

def run_migration(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION;")

        # --- Step 1: Users table extensions ---
        user_cols = [r[1] for r in cursor.execute("PRAGMA table_info(users);").fetchall()]
        
        if "phone" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(30);")
        if "email" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(150);")
        if "hashed_password" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255);")
        if "token_version" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 1;")
        if "is_active" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1;")
        if "is_phone_verified" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_phone_verified BOOLEAN NOT NULL DEFAULT 0;")
        if "failed_login_attempts" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;")
        if "locked_until" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until DATETIME;")
        if "updated_at" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME;")

        # Unique partial indexes on users
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone) WHERE phone IS NOT NULL;")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;")

        # Non-recursive trigger for raw SQL insert updated_at default
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_users_updated_at_default
        AFTER INSERT ON users
        FOR EACH ROW
        WHEN NEW.updated_at IS NULL
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        """)

        # --- Step 2: Incidents table extensions ---
        inc_cols = [r[1] for r in cursor.execute("PRAGMA table_info(incidents);").fetchall()]
        if "tracking_token_hash" not in inc_cols:
            cursor.execute("ALTER TABLE incidents ADD COLUMN tracking_token_hash VARCHAR(64);")
        if "public_reference" not in inc_cols:
            cursor.execute("ALTER TABLE incidents ADD COLUMN public_reference VARCHAR(32);")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_tracking_hash ON incidents(tracking_token_hash) WHERE tracking_token_hash IS NOT NULL;")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_public_ref ON incidents(public_reference) WHERE public_reference IS NOT NULL;")

        # --- Step 3: New table: user_sessions ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(64) NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            refresh_token_hash VARCHAR(64) NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            last_used_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            revoked_at DATETIME,
            is_revoked BOOLEAN NOT NULL DEFAULT 0,
            replaced_by_session_id VARCHAR(64),
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_lookup ON user_sessions(refresh_token_hash, is_revoked);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id, is_revoked);")

        # --- Step 4: New table: volunteer_profiles ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS volunteer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            legacy_volunteer_id INTEGER UNIQUE,
            skills TEXT,
            sector VARCHAR(150),
            availability VARCHAR(30) NOT NULL DEFAULT 'offline',
            approval_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (legacy_volunteer_id) REFERENCES volunteers(id) ON DELETE SET NULL
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vol_profile_avail ON volunteer_profiles(availability, approval_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vol_profile_sector ON volunteer_profiles(sector);")

        # --- Step 5: New table: incident_assignments ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            volunteer_profile_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            accepted_at DATETIME,
            rejected_at DATETIME,
            completed_at DATETIME,
            rejection_reason TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE RESTRICT,
            FOREIGN KEY (volunteer_profile_id) REFERENCES volunteer_profiles(id) ON DELETE RESTRICT,
            FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignment_incident ON incident_assignments(incident_id, status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignment_volunteer ON incident_assignments(volunteer_profile_id, status);")
        
        # Ensure only one active/pending assignment exists per incident
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_assignment_per_incident 
        ON incident_assignments(incident_id) 
        WHERE status IN ('PENDING', 'ACCEPTED');
        """)

        # --- Step 6: New table: incident_status_history ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            previous_status VARCHAR(30) NOT NULL,
            new_status VARCHAR(30) NOT NULL,
            changed_by INTEGER,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE RESTRICT,
            FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_history_inc ON incident_status_history(incident_id, timestamp);")

        # --- Step 7: New table: audit_logs ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            target_id VARCHAR(50),
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            previous_hash VARCHAR(64),
            current_hash VARCHAR(64) NOT NULL,
            FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action_ts ON audit_logs(action, timestamp);")

        # Triggers preventing audit_logs update/delete
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_audit_update
        BEFORE UPDATE ON audit_logs
        BEGIN
            SELECT RAISE(ABORT, 'Integrity Violation: audit_logs rows are append-only.');
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_prevent_audit_delete
        BEFORE DELETE ON audit_logs
        BEGIN
            SELECT RAISE(ABORT, 'Integrity Violation: audit_logs rows cannot be deleted.');
        END;
        """)

        # Foreign Key check before commit
        fk_violations = cursor.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_violations:
            raise RuntimeError(f"Foreign key integrity violated during migration: {fk_violations}")

        conn.commit()
        print("MIGRATION_COMPLETED_SUCCESSFULLY")

    except Exception as e:
        conn.rollback()
        print(f"MIGRATION_FAILED_ROLLEDBACK: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else "warkari.db"
    run_migration(target_db)

