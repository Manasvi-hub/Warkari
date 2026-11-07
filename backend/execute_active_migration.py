import sqlite3
from backend.migrations.migrate_phase4_1 import run_migration

def migrate_active():
    print('--- EXECUTING ACTIVE DATABASE MIGRATION ---')
    run_migration('warkari.db')

    conn = sqlite3.connect('warkari.db')
    c = conn.cursor()

    fac_count = c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0]
    inc_count = c.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
    historical_open = c.execute("SELECT COUNT(*) FROM incidents WHERE status = 'OPEN'").fetchone()[0]
    null_hashes = c.execute('SELECT COUNT(*) FROM incidents WHERE tracking_token_hash IS NULL').fetchone()[0]
    null_refs = c.execute('SELECT COUNT(*) FROM incidents WHERE public_reference IS NULL').fetchone()[0]
    min_id, max_id = c.execute('SELECT MIN(id), MAX(id) FROM incidents').fetchone()
    fks = c.execute('PRAGMA foreign_key_check').fetchall()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

    print('--- ACTIVE DATABASE POST-MIGRATION REPORT ---')
    print('TABLES:', tables)
    print('FACILITY_COUNT:', fac_count)
    print('INCIDENT_COUNT:', inc_count)
    print('HISTORICAL_INCIDENT_RANGE:', min_id, 'to', max_id)
    print('HISTORICAL_OPEN_COUNT:', historical_open)
    print('NULL_TRACKING_HASHES:', null_hashes)
    print('NULL_PUBLIC_REFS:', null_refs)
    print('FK_VIOLATIONS:', len(fks))

    assert fac_count == 5
    assert inc_count == 138
    assert historical_open == 138
    assert null_hashes == 138
    assert null_refs == 138
    assert len(fks) == 0
    print('ACTIVE DATABASE MIGRATION VERIFIED SUCCESSFULLY!')
    conn.close()

if __name__ == '__main__':
    migrate_active()

