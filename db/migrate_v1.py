import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_CONFIG = {
    "host": "database-1.cz6yc6aasf2z.us-west-2.rds.amazonaws.com",
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgress",
    "port": 5432,
    "sslmode": "require"
}

def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def migrate():
    conn = get_conn()
    cur = conn.cursor()
    
    print("🔄 Starting database migration...")

    # 1. Update CALLS table
    try:
        cur.execute("ALTER TABLE calls ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'UPLOADED';")
        print("✅ Added 'status' column to calls.")
    except Exception as e:
        print(f"⚠️ Could not add status column: {e}")

    # Make score columns nullable (since we insert pending calls now)
    cols_to_nullable = ["qa_score", "qa_band", "sentiment_trend", "is_good_call"]
    for col in cols_to_nullable:
        try:
            cur.execute(f"ALTER TABLE calls ALTER COLUMN {col} DROP NOT NULL;")
            print(f"✅ Altered {col} to be nullable.")
        except Exception as e:
            print(f"⚠️ Could not alter {col}: {e}")

    # 2. Update SUPERVISOR_ALERTS table
    # Since schema changed significantly (PK changed), we'll drop and recreate for dev environment
    try:
        cur.execute("DROP TABLE IF EXISTS supervisor_alerts;")
        cur.execute("""
            CREATE TABLE supervisor_alerts (
                alert_id SERIAL PRIMARY KEY,
                call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
                alert_level TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'NEW',
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✅ Recreated supervisor_alerts table with new schema.")
    except Exception as e:
        print(f"❌ Failed to recreate supervisor_alerts: {e}")

    # 3. Create CALL_NOTES table
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS call_notes (
                note_id SERIAL PRIMARY KEY,
                call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
                note_text TEXT NOT NULL,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("✅ Created call_notes table.")
    except Exception as e:
        print(f"❌ Failed to create call_notes: {e}")

    cur.close()
    conn.close()
    print("✨ Migration complete.")

if __name__ == "__main__":
    migrate()
