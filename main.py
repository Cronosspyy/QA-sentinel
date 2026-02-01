import os
import json
from datetime import datetime, timezone

# ---------------- PIPELINE IMPORTS ----------------
from pipelines.audio_ingestion import process_audio_directory
from pipelines.transcript_structurer import process_transcripts_folder

from qa_engine.rule_engine import run_rule_engine
from assistive_ai.sentiment_trajectory import build_sentiment_trajectory
from qa_engine.qa_scorer import score_call
from qa_engine.good_call_policy import is_good_call

from risk_engine.supervisor_alerts import generate_supervisor_alert

from db.repository import save_call


# ---------------- CONFIG ----------------
AUDIO_DIR = "data/audio"
RAW_TRANSCRIPTS_DIR = "transcripts/aws_raw"
PARSED_TRANSCRIPTS_DIR = "transcripts/parsed"
S3_BUCKET = "qa-call-audio"


# ---------------- HELPERS ----------------
def load_structured_calls(parsed_dir):
    calls = []
    for fname in os.listdir(parsed_dir):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(parsed_dir, fname), "r", encoding="utf-8") as f:
            calls.append(json.load(f))
    return calls


# ---------------- MAIN ----------------
def main():
    print("=" * 70)
    print("📞 AUTO-QA CALL ANALYSIS PIPELINE STARTED")
    print("=" * 70)

    # STEP 1 — AUDIO → TRANSCRIPT
    print("\n🔊 Step 1: Audio ingestion & transcription")
    process_audio_directory(
        input_dir=AUDIO_DIR,
        s3_bucket=S3_BUCKET,
        output_dir=RAW_TRANSCRIPTS_DIR
    )

    # STEP 2 — STRUCTURE TRANSCRIPTS
    print("\n🧠 Step 2: Structuring transcripts")
    process_transcripts_folder(
        input_dir=RAW_TRANSCRIPTS_DIR,
        output_dir=PARSED_TRANSCRIPTS_DIR
    )

    # STEP 3 — LOAD STRUCTURED CALLS
    print("\n📂 Step 3: Loading structured calls")
    calls = load_structured_calls(PARSED_TRANSCRIPTS_DIR)

    if not calls:
        print("⚠️ No calls found. Exiting.")
        return

    print(f"✅ Loaded {len(calls)} calls")

    # STEP 4 — ANALYZE EACH CALL
    print("\n🧪 Step 4: Running QA analysis per call\n")

    for idx, call in enumerate(calls, start=1):
        call_id = call["call_id"]
        agent_id = call.get("agent_id")
        city = call.get("city")

        print("-" * 70)
        print(f"📞 Call {idx}: {call_id}")

        # RULE ENGINE
        rule_result = run_rule_engine(call)

        # SENTIMENT
        sentiment_result = build_sentiment_trajectory(call)

        # QA SCORE
        qa_result = score_call(rule_result, sentiment_result)

        # GOOD CALL?
        good_call = is_good_call(
            qa_result=qa_result,
            rule_result=rule_result,
            sentiment_result=sentiment_result
        )

        # SUPERVISOR ALERT
        alert = generate_supervisor_alert({
            "qa_result": qa_result,
            "sentiment_result": sentiment_result,
            "rule_result": rule_result
        })

        # PRINT SUMMARY
        print(f"📊 QA Score: {qa_result['qa_score']} ({qa_result['band']})")
        print(f"✅ Good Call: {good_call}")

        if alert:
            print(f"🚨 ALERT: {alert['level']} — {alert['action']}")

        # SAVE TO DB
        save_call(
            call={
                "call_id": call_id,
                "agent_id": agent_id,
                "city": city,
                "call_time": datetime.now(timezone.utc)

            },
            qa_result=qa_result,
            sentiment_result=sentiment_result,
            is_good_call=good_call,
            alert=alert
        )

    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETE — ALL CALLS PROCESSED & STORED")
    print("=" * 70)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    main()
