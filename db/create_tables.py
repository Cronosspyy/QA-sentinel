import psycopg2

# ----------------------------
# UPDATE THESE VALUES
# ----------------------------
DB_CONFIG = {
    "host": "database-1.cz6yc6aasf2z.us-west-2.rds.amazonaws.com",
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgress",
    "port": 5432,
}

DDL_STATEMENTS = [

    # ----------------------------
    # CALLS
    # ----------------------------
    """
    CREATE TABLE IF NOT EXISTS calls (
        call_id TEXT PRIMARY KEY,
        agent_id TEXT,
        city TEXT,
        call_time TIMESTAMP,
        status TEXT DEFAULT 'UPLOADED',
        qa_score INT,
        qa_band TEXT,
        sentiment_trend TEXT,
        is_good_call BOOLEAN,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,

    # ----------------------------
    # QA BREAKDOWN
    # ----------------------------
    """
    CREATE TABLE IF NOT EXISTS qa_breakdown (
        call_id TEXT PRIMARY KEY REFERENCES calls(call_id) ON DELETE CASCADE,
        process_score INT NOT NULL,
        resolution_score INT NOT NULL,
        sentiment_score INT NOT NULL,
        compliance_score INT NOT NULL
    );
    """,

    # ----------------------------
    # QA EXPLANATIONS
    # ----------------------------
    """
    CREATE TABLE IF NOT EXISTS qa_explanations (
        id SERIAL PRIMARY KEY,
        call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
        reason TEXT NOT NULL
    );
    """,

    # ----------------------------
    # SUPERVISOR ALERTS
    # ----------------------------
    """
    CREATE TABLE IF NOT EXISTS supervisor_alerts (
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
    """,

    # ----------------------------
    # CALL NOTES
    # ----------------------------
    """
    CREATE TABLE IF NOT EXISTS call_notes (
        note_id SERIAL PRIMARY KEY,
        call_id TEXT REFERENCES calls(call_id) ON DELETE CASCADE,
        note_text TEXT NOT NULL,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
]

def main():
    print("🔌 Connecting to Postgres...")
    # conn = psycopg2.connect(**DB_CONFIG)
    conn = psycopg2.connect(
    host="database-1.cz6yc6aasf2z.us-west-2.rds.amazonaws.com",
    dbname="postgres",
    user="postgres",
    password="postgress",
    port=5432,
    sslmode="require"
)

    cur = conn.cursor()

    for ddl in DDL_STATEMENTS:
        cur.execute(ddl)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ All tables created successfully.")

if __name__ == "__main__":
    main()
