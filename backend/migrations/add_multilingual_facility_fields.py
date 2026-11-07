"""Dedicated idempotent database migration script for Phase 3.3.5.

Safeguards strictly enforced:
- Idempotent: detects whether each column already exists before attempting ALTER TABLE.
- Adds only the six approved nullable columns:
  name_en, name_hi, location_en, location_hi, description_en, description_hi
- Never drops or recreates facilities table.
- Never modifies existing facility names, locations, or descriptions.
- Never modifies incidents table or touches foreign keys.
- Never alters is_demo, is_verified, source or operational_status.
- Leaves all six new columns NULL.
"""

import sqlite3
import os
import sys

APPROVED_NEW_COLUMNS = [
    ("name_en", "VARCHAR(150)"),
    ("name_hi", "VARCHAR(150)"),
    ("location_en", "VARCHAR(255)"),
    ("location_hi", "VARCHAR(255)"),
    ("description_en", "TEXT"),
    ("description_hi", "TEXT"),
]


def run_migration(db_path: str = "warkari.db"):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # Pre-check existing columns
        c.execute("PRAGMA table_info(facilities)")
        existing_cols = {col[1]: col for col in c.fetchall()}

        # Verify baseline table integrity
        c.execute("SELECT count(*) FROM facilities")
        fac_count = c.fetchone()[0]
        c.execute("SELECT count(*) FROM incidents")
        inc_count = c.fetchone()[0]

        if fac_count != 5:
            raise ValueError(f"Pre-migration check failed: expected 5 facilities, found {fac_count}")
        if inc_count != 81:
            raise ValueError(f"Pre-migration check failed: expected 81 incidents, found {inc_count}")

        # Check FK integrity
        c.execute("PRAGMA foreign_key_check")
        fk_issues = c.fetchall()
        if fk_issues:
            raise ValueError(f"Pre-migration foreign key issues: {fk_issues}")

        added_columns = []
        for col_name, col_type in APPROVED_NEW_COLUMNS:
            if col_name not in existing_cols:
                # Add missing column
                alter_sql = f"ALTER TABLE facilities ADD COLUMN {col_name} {col_type}"
                print(f"Executing: {alter_sql}")
                c.execute(alter_sql)
                added_columns.append(col_name)
            else:
                print(f"Column '{col_name}' already exists. Skipping.")

        conn.commit()
        print(f"Migration completed successfully. Added columns: {added_columns}")

        # Post-migration verification
        c.execute("PRAGMA table_info(facilities)")
        updated_cols = {col[1]: col for col in c.fetchall()}
        for col_name, _ in APPROVED_NEW_COLUMNS:
            if col_name not in updated_cols:
                raise ValueError(f"Post-migration check failed: column '{col_name}' is missing!")

        # Verify all new fields are NULL across all 5 facilities
        c.execute("""
            SELECT id, name_en, name_hi, location_en, location_hi, description_en, description_hi
            FROM facilities ORDER BY id
        """)
        rows = c.fetchall()
        for r in rows:
            for val in r[1:]:
                if val is not None:
                    raise ValueError(f"Expected NULL in new translation field for facility {r[0]}, found {val}")

        # Verify count and IDs 1 to 5 intact
        c.execute("SELECT count(*) FROM facilities")
        post_fac_count = c.fetchone()[0]
        c.execute("SELECT count(*) FROM incidents")
        post_inc_count = c.fetchone()[0]

        if post_fac_count != 5 or post_inc_count != 81:
            raise ValueError(f"Count mismatch post-migration: facs={post_fac_count}, incs={post_inc_count}")

        c.execute("PRAGMA foreign_key_check")
        post_fk = c.fetchall()
        if post_fk:
            raise ValueError(f"Post-migration foreign key check failed: {post_fk}")

        print("All post-migration verifications PASSED successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Migration ERROR: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "warkari.db"
    run_migration(db_file)

