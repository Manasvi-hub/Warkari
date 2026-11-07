import sqlite3

def migrate():
    conn = sqlite3.connect("warkari.db")
    cursor = conn.cursor()

    def add_col_if_missing(table, col_name, col_def):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if col_name not in columns:
            print(f"Adding {col_name} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
            print(f"Added {col_name} successfully.")
        else:
            print(f"{col_name} already exists in {table}.")

    # Facilities extensions
    add_col_if_missing("facilities", "description", "TEXT")
    add_col_if_missing("facilities", "contact_phone", "VARCHAR(50)")
    add_col_if_missing("facilities", "is_verified", "BOOLEAN NOT NULL DEFAULT 0")
    add_col_if_missing("facilities", "is_demo", "BOOLEAN NOT NULL DEFAULT 0")

    # Incidents extensions
    add_col_if_missing("incidents", "original_message", "TEXT")
    add_col_if_missing("incidents", "language", "VARCHAR(20) NOT NULL DEFAULT 'mr-IN'")
    add_col_if_missing("incidents", "urgency_level", "VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'")
    add_col_if_missing("incidents", "location_description", "VARCHAR(255)")
    add_col_if_missing("incidents", "latitude", "FLOAT")
    add_col_if_missing("incidents", "longitude", "FLOAT")
    add_col_if_missing("incidents", "updated_at", "DATETIME")

    conn.commit()
    conn.close()
    print("Schema migration finished successfully.")

if __name__ == "__main__":
    migrate()

