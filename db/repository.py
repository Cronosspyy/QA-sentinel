import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

def get_conn():
    return psycopg2.connect(
        host="database-1.cz6yc6aasf2z.us-west-2.rds.amazonaws.com",
        dbname="postgres",
        user="postgres",
        password="postgress",
        port=5432,
        sslmode="require",
        cursor_factory=RealDictCursor
    )

# ---------------- INGESTION ----------------

def create_pending_call(call_id, agent_id=None, city=None, call_time=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO calls (call_id, agent_id, city, call_time, status)
            VALUES (%s, %s, %s, %s, 'UPLOADED')
            ON CONFLICT (call_id) DO NOTHING
        """, (call_id, agent_id, city, call_time))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_call_status(call_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT status FROM calls WHERE call_id = %s", (call_id,))
        row = cur.fetchone()
        return row['status'] if row else None
    finally:
        cur.close()
        conn.close()

def update_call_status(call_id, status):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE calls SET status = %s WHERE call_id = %s", (status, call_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()

def save_call_results(call_id, qa_result, sentiment_result, is_good_call, alert):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Update main call record
        cur.execute("""
            UPDATE calls
            SET qa_score = %s, qa_band = %s, sentiment_trend = %s, is_good_call = %s, status = 'PROCESSED'
            WHERE call_id = %s
        """, (
            qa_result["qa_score"],
            qa_result["band"],
            sentiment_result["trend"],
            is_good_call,
            call_id
        ))

        # Insert QA breakdown
        cur.execute("DELETE FROM qa_breakdown WHERE call_id = %s", (call_id,))
        cur.execute("""
            INSERT INTO qa_breakdown (call_id, process_score, resolution_score, sentiment_score, compliance_score)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            call_id,
            qa_result["breakdown"]["process"],
            qa_result["breakdown"]["resolution"],
            qa_result["breakdown"]["sentiment"],
            qa_result["breakdown"]["compliance"]
        ))

        # Insert QA explanations
        cur.execute("DELETE FROM qa_explanations WHERE call_id = %s", (call_id,))
        for reason in qa_result.get("explanations", []):
            cur.execute("INSERT INTO qa_explanations (call_id, reason) VALUES (%s, %s)", (call_id, reason))

        # Supervisor Alert
        if alert:
            cur.execute("""
                INSERT INTO supervisor_alerts (call_id, alert_level, reason, status)
                VALUES (%s, %s, %s, 'NEW')
            """, (call_id, alert["level"], alert["action"]))
        
        conn.commit()
    finally:
        cur.close()
        conn.close()

# ---------------- DASHBOARD ----------------

def get_org_summary(days=30):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                AVG(qa_score) as avg_qa_score,
                COUNT(*) as total_calls,
                COALESCE(COUNT(CASE WHEN qa_band = 'High Risk' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 0) as high_risk_pct
            FROM calls
            WHERE call_time >= NOW() - INTERVAL '%s days'
        """, (days,))
        stats = cur.fetchone()

        cur.execute("""
            SELECT COUNT(*) as alert_volume
            FROM supervisor_alerts
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """, (days,))
        alerts = cur.fetchone()
        
        return {**stats, **alerts} if stats else None
    finally:
        cur.close()
        conn.close()

def get_qa_trend(days=30):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DATE(call_time) as date, AVG(qa_score) as avg_score
            FROM calls
            WHERE call_time >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(call_time)
            ORDER BY DATE(call_time)
        """, (days,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_qa_distribution(weeks=4):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Simplified: just return counts by band for last N weeks
        cur.execute("""
            SELECT qa_band, COUNT(*) as count
            FROM calls
            WHERE call_time >= NOW() - INTERVAL '%s weeks'
            GROUP BY qa_band
        """, (weeks,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# ---------------- ALERTS ----------------

def get_alerts(risk_level=None, days=1):
    conn = get_conn()
    cur = conn.cursor()
    try:
        query = """
            SELECT a.*, c.agent_id, c.qa_score
            FROM supervisor_alerts a
            JOIN calls c ON a.call_id = c.call_id
            WHERE a.created_at >= NOW() - INTERVAL '%s days'
        """
        params = [days]
        if risk_level:
            query += " AND a.alert_level = %s"
            params.append(risk_level)
            
        cur.execute(query, tuple(params))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def acknowledge_alert(alert_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE supervisor_alerts
            SET status = 'ACKNOWLEDGED', acknowledged_by = %s, acknowledged_at = NOW()
            WHERE alert_id = %s
            RETURNING *
        """, (user_id, alert_id))
        conn.commit()
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def resolve_alert(alert_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE supervisor_alerts
            SET status = 'RESOLVED', resolved_at = NOW()
            WHERE alert_id = %s
            RETURNING *
        """, (alert_id,))
        conn.commit()
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

# ---------------- AGENTS ----------------

def get_agents():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT agent_id FROM calls WHERE agent_id IS NOT NULL")
        return [row['agent_id'] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def get_agent_scorecard(agent_id, days=30):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                AVG(qa_score) as avg_qa,
                COUNT(*) as call_count,
                COALESCE(COUNT(CASE WHEN is_good_call THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 0) as good_call_pct
            FROM calls
            WHERE agent_id = %s AND call_time >= NOW() - INTERVAL '%s days'
        """, (agent_id, days))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def get_agent_coaching_insights(agent_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Aggregate logic based on qa_explanations for this agent
        cur.execute("""
            SELECT e.reason, COUNT(*) as count
            FROM qa_explanations e
            JOIN calls c ON e.call_id = c.call_id
            WHERE c.agent_id = %s
            GROUP BY e.reason
            ORDER BY count DESC
            LIMIT 5
        """, (agent_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_agent_calls(agent_id, limit=20):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM calls
            WHERE agent_id = %s
            ORDER BY call_time DESC
            LIMIT %s
        """, (agent_id, limit))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# ---------------- CALL DETAILS ----------------

def get_all_calls(limit=50):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM calls
            ORDER BY call_time DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_call_detail(call_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calls WHERE call_id = %s", (call_id,))
        call = cur.fetchone()
        if not call:
            return None
        
        cur.execute("SELECT * FROM qa_breakdown WHERE call_id = %s", (call_id,))
        breakdown = cur.fetchone()
        
        cur.execute("SELECT reason FROM qa_explanations WHERE call_id = %s", (call_id,))
        explanations = [row['reason'] for row in cur.fetchall()]
        
        return {
            "metadata": call,
            "qa_breakdown": breakdown,
            "explanations": explanations
        }
    finally:
        cur.close()
        conn.close()

def save_supervisor_note(call_id, note_text, created_by="Supervisor"):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO call_notes (call_id, note_text, created_by)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (call_id, note_text, created_by))
        conn.commit()
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
