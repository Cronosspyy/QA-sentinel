import psycopg2

def get_conn():
    return psycopg2.connect(
        host="database-1.cz6yc6aasf2z.us-west-2.rds.amazonaws.com",
        dbname="postgres",
        user="postgres",
        password="postgress",
        port=5432,
        sslmode="require"
    )

def save_call(call, qa_result, sentiment_result, is_good_call, alert):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO calls (
            call_id, agent_id, city, call_time,
            qa_score, qa_band, sentiment_trend, is_good_call
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (call_id) DO NOTHING
    """, (
        call["call_id"],
        call.get("agent_id"),
        call.get("city"),
        call.get("call_time"),
        qa_result["qa_score"],
        qa_result["band"],
        sentiment_result["trend"],
        is_good_call
    ))
