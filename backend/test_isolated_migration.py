import shutil
import sqlite3
from backend.migrations.migrate_phase4_1 import run_migration

def test_isolated_migration():
    shutil.copy2('warkari.db', 'warkari_test_migration.db')
    print('Running migration on isolated test database...')
    run_migration('warkari_test_migration.db')

    conn = sqlite3.connect('warkari_test_migration.db')
    c = conn.cursor()
    fac_count = c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0]
    inc_count = c.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
    null_hashes = c.execute('SELECT COUNT(*) FROM incidents WHERE tracking_token_hash IS NULL').fetchone()[0]
    null_refs = c.execute('SELECT COUNT(*) FROM incidents WHERE public_reference IS NULL').fetchone()[0]
    statuses = [r[0] for r in c.execute('SELECT DISTINCT status FROM incidents').fetchall()]
    fks = c.execute('PRAGMA foreign_key_check').fetchall()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

    print('VERIFICATION RESULTS:')
    print('TABLES:', tables)
    print('FACILITIES:', fac_count)
    print('INCIDENTS:', inc_count)
    print('HISTORICAL NULL HASHES:', null_hashes)
    print('HISTORICAL NULL REFS:', null_refs)
    print('STATUSES:', statuses)
    print('FK_VIOLATIONS:', len(fks))

    assert fac_count == 5, f"Expected 5 facilities, got {fac_count}"
    assert inc_count == 138, f"Expected 138 incidents, got {inc_count}"
    assert null_hashes == 138, "All historical incidents must have NULL tracking_token_hash"
    assert null_refs == 138, "All historical incidents must have NULL public_reference"
    assert statuses == ['OPEN'], f"Historical incidents must remain OPEN, got {statuses}"
    assert len(fks) == 0, f"Foreign key violations found: {fks}"
    assert 'user_sessions' in tables
    assert 'volunteer_profiles' in tables
    assert 'incident_assignments' in tables
    assert 'incident_status_history' in tables
    assert 'audit_logs' in tables
    print('ALL ISOLATED MIGRATION CHECKS PASSED!')
    conn.close()

if __name__ == '__main__':
    test_isolated_migration()

