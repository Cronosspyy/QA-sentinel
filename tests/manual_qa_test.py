# from pipelines.transcript_structurer import process_transcripts_folder
# from pipelines.audio_ingestion import process_audio_directory
# from qa_engine.rule_engine import run_rule_engine

# # # Step 1 : Save the audio file in the data/audio directory

# process_audio_directory(
#         input_dir="data/audio",
#         s3_bucket="qa-call-audio",
#         output_dir="transcripts/aws_raw"
# )

# # Step 2: Structure JSON

# process_transcripts_folder(
#         input_dir="transcripts/aws_raw",
#         output_dir="transcripts/parsed"
#     )
# # RUle Run 
# print(run_rule_engine(structured_call))


# # Sentiment Trajectory

# from assistive_ai.sentiment_trajectory import build_sentiment_trajectory

# structured_call = {
#     "turns": [
#         {"speaker": "Customer", "start": 5, "end": 10, "text": "This is very frustrating"},
#         {"speaker": "Customer", "start": 40, "end": 50, "text": "Okay, I understand now"},
#         {"speaker": "Customer", "start": 80, "end": 90, "text": "Thanks, that helps"}
#     ]
# }

# # print(build_sentiment_trajectory(structured_call))
# from risk_engine.risk_flagger import compute_risk
# risk_result = compute_risk(
#     call_id=structured_call["call_id"],
#     rule_result=rule_engine_output,
#     sentiment_result=sentiment_output
# )

# print(risk_result)


import os
import json

from pipelines.audio_ingestion import process_audio_directory
from pipelines.transcript_structurer import process_transcripts_folder
from qa_engine.rule_engine import run_rule_engine
from assistive_ai.sentiment_trajectory import build_sentiment_trajectory
from risk_engine.risk_flagger import compute_risk

from qa_engine.qa_scorer import score_call

AUDIO_DIR = "data/audio"
RAW_TRANSCRIPTS_DIR = "transcripts/aws_raw"
PARSED_TRANSCRIPTS_DIR = "transcripts/parsed"
S3_BUCKET = "qa-call-audio"


def load_structured_calls(parsed_dir):
    calls = []

    for fname in os.listdir(parsed_dir):
        if not fname.endswith(".json"):
            continue

        path = os.path.join(parsed_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            call = json.load(f)

        calls.append(call)

    return calls


def main():
    print("=" * 60)
    print("📞 QA CALL ANALYSIS PIPELINE STARTED")
    print("=" * 60)

    # Step 1: Audio ingestion + transcription
    print("\n🔊 Step 1: Processing audio files...")
    process_audio_directory(
        input_dir=AUDIO_DIR,
        s3_bucket=S3_BUCKET,
        output_dir=RAW_TRANSCRIPTS_DIR
    )
    print("✅ Audio ingestion complete.")

    # Step 2: Transcript structuring
    print("\n🧠 Step 2: Structuring transcripts...")
    process_transcripts_folder(
        input_dir=RAW_TRANSCRIPTS_DIR,
        output_dir=PARSED_TRANSCRIPTS_DIR
    )
    print("✅ Transcript structuring complete.")

    # Step 3: Load structured calls
    print("\n📂 Step 3: Loading structured calls...")
    structured_calls = load_structured_calls(PARSED_TRANSCRIPTS_DIR)
    print(f"✅ Loaded {len(structured_calls)} calls.")

    if not structured_calls:
        print("⚠️ No structured calls found. Exiting.")
        return

    # Step 4–6: Run analysis per call
    print("\n🧪 Step 4: Running analysis per call...\n")

    for i, call in enumerate(structured_calls, start=1):
        call_id = call.get("call_id", f"call_{i}")

        print("-" * 60)
        print(f"📞 Call {i}: {call_id}")

        # Rule Engine
        print("📐 Running rule engine...")
        rule_result = run_rule_engine(call)
        print(f"   Rule result: {rule_result}")

        # Sentiment Trajectory
        print("💭 Analyzing sentiment trajectory...")
        sentiment_result = build_sentiment_trajectory(call)
        print(f"   Sentiment: {sentiment_result}")

        # Risk Computation
        print("⚠️ Computing risk...")
        risk_result = compute_risk(
            call_id=call_id,
            rule_result=rule_result,
            sentiment_result=sentiment_result
        )
        print(f"   🚨 Risk result: {risk_result}")

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # main()
    Sentiment= {'sentiment_windows': [0.25, 0.2, 0.33, 0.25, 0.5], 'trend': 'STABLE'}
    rule_result = run_rule_engine({
  "call_id": "jyoti_srv_saraviconsultants_co_in__Driver_and_Partner_Support__342__168624416__7248888738__2026-01-29_13-43-09-1769880773",
  "source": "aws_transcribe",
  "speaker_map": {
    "spk_0": "Agent",
    "spk_1": "Customer"
  },
  "summary": {
    "num_turns": 22,
    "interruptions": 0,
    "duration_sec": 111.709
  },
  "turns": [
    {
      "turn_id": 1,
      "speaker": "Agent",
      "start": 2.14,
      "end": 2.89,
      "text": "Hello",
      "silence_after": 1.04,
      "phase": "OPENING"
    },
    {
      "turn_id": 2,
      "speaker": "Customer",
      "start": 3.93,
      "end": 7.46,
      "text": "नमस्कार सिर में आपका स्वागत है मैं ज्योति आपकी क्या सहायता कर सकती हूँ",
      "silence_after": 2.26,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 3,
      "speaker": "Agent",
      "start": 9.72,
      "end": 14.659,
      "text": "मैंने मैं बोल रहा हूँ मेरी battery ID है double one six eight eight",
      "silence_after": 0.8,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 4,
      "speaker": "Customer",
      "start": 15.46,
      "end": 19.229,
      "text": "आपकी driver ID double one six double eight three नाम बता दीजिए किस नाम से है आप",
      "silence_after": 1.11,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 5,
      "speaker": "Agent",
      "start": 20.34,
      "end": 21.969,
      "text": "आर्यन",
      "silence_after": 1.2,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 6,
      "speaker": "Customer",
      "start": 23.17,
      "end": 25.11,
      "text": "आर्यन तुलसी जी के नाम से आप जी बताइए क्या सहायता कर सकती हूँ आपकी",
      "silence_after": 2.08,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 7,
      "speaker": "Agent",
      "start": 27.19,
      "end": 28.239,
      "text": "नहीं मैंने कर लिया",
      "silence_after": 1.14,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 8,
      "speaker": "Customer",
      "start": 29.379,
      "end": 29.909,
      "text": "जी",
      "silence_after": 1.5,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 9,
      "speaker": "Agent",
      "start": 31.409,
      "end": 31.44,
      "text": "थोड़ी",
      "silence_after": 2.67,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 10,
      "speaker": "Customer",
      "start": 34.11,
      "end": 35.849,
      "text": "थोड़ी देर पहले बैठी ली थी आपने",
      "silence_after": 2.19,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 11,
      "speaker": "Customer",
      "start": 38.04,
      "end": 40.299,
      "text": "आपने सब swap लिया था एक बजकर पांच मिनट पे",
      "silence_after": 1.17,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 12,
      "speaker": "Agent",
      "start": 41.47,
      "end": 42.279,
      "text": "हाँ जी हाँ जी",
      "silence_after": 0.59,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 13,
      "speaker": "Customer",
      "start": 42.869,
      "end": 45.54,
      "text": "और अभी क्या दिक्कत आ रही है आपको बैटरी जल्दी discharge हो रही है आपकी",
      "silence_after": 2.01,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 14,
      "speaker": "Customer",
      "start": 47.549,
      "end": 51.459,
      "text": "अभी सिर आपको एक घंटा भी नहीं हुआ है कि कितना चार्ज है अभी बैट में आपके",
      "silence_after": 2.1,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 15,
      "speaker": "Agent",
      "start": 53.56,
      "end": 54.959,
      "text": "मेरी पचहत्तर पर्सेंट हो गया है",
      "silence_after": 0.44,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 16,
      "speaker": "Customer",
      "start": 55.4,
      "end": 62.99,
      "text": "पचहत्तर पर्सेंट है ना सिर अभी चार्ज आपको एक घंटा भी नहीं हुआ अभी आप थोड़ी देर और चला लीजिए बैठे आधे घंटे और जल्दी डिस्चार्ज होने लगेगी तो कॉल कर लीजिएगा आप हमें",
      "silence_after": 3.6,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 17,
      "speaker": "Customer",
      "start": 66.589,
      "end": 72.959,
      "text": "हाँ जी अभी आप उस टाइम उसे कर लीजिए बैटरी को अगर जल्दी discharge होने लगेगी आप हमें कर दीजिएगा कोई और सहायता आपकी battery smart से सम्बंधित है",
      "silence_after": 1.51,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 18,
      "speaker": "Agent",
      "start": 74.47,
      "end": 75.069,
      "text": "नहीं नहीं",
      "silence_after": 1.21,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 19,
      "speaker": "Customer",
      "start": 76.279,
      "end": 85.809,
      "text": "आपकी कॉल को आईवीआर पे फीडबैक के लिए ट्रांसफर कर रही हूँ अगर आप दी गई जानकारी से सहमत है तो एक दबा दीजिये और सिर अगर आप सहमत नहीं है तो दो दबा दीजिये में कॉल करने के लिए धन्यवाद सिर स्वस्थ रहिए सुरक्षित रहिए",
      "silence_after": 1.43,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 20,
      "speaker": "Customer",
      "start": 87.239,
      "end": 92.83,
      "text": "अगर आप हमारे द्वारा दी गई सहायता से खुश हैं तो एक दबाएं अगर नहीं तो दो दबाएं",
      "silence_after": 5.26,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 21,
      "speaker": "Customer",
      "start": 98.089,
      "end": 101.4,
      "text": "आपकी तरफ से कोई भी चुनाव नहीं किया गया है",
      "silence_after": 1.34,
      "phase": "RESOLUTION"
    },
    {
      "turn_id": 22,
      "speaker": "Customer",
      "start": 102.739,
      "end": 111.709,
      "text": "अगर आप हमारे द्वारा दी गई सहायता से खुश है तो एक दवा आपकी प्रतिक्रिया हमारे लिए बहुत मायने रखती है बैटरी स्मार्ट चुनने के लिए धन्यवाद",
      "silence_after": 0.0,
      "phase": "RESOLUTION"
    }
  ]
})

    qa_result = score_call(rule_result, Sentiment)
    
    print(f"📊 QA Score: {qa_result}")

    from qa_engine.good_call_policy import is_good_call

    good_call = is_good_call(qa_result, rule_result, Sentiment)

    print(f"✅ Good Call: {good_call}")


    from risk_engine.supervisor_alerts import generate_supervisor_alert

    alert = generate_supervisor_alert({
        "qa_result": qa_result,
        "sentiment_result": Sentiment,
        "rule_result": rule_result
    })

    if alert:
        print(f"🚨 SUPERVISOR ALERT: {alert}")


