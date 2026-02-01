import requests
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"
AUDIO_FILE = "D:\\hacksmart\\data\\audio\\jyoti_srv_saraviconsultants_co_in__Driver_and_Partner_Support__342__168624416__7248888738__2026-01-29_13-43-09.mp3"

def pretty(title, obj):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print(obj)


# 1️⃣ Upload audio
def upload_audio():
    files = {
        "file": open(AUDIO_FILE, "rb")
    }
    data = {
        "agent_id": "agent_001",
        "city": "Bangalore"
    }

    r = requests.post(
        f"{BASE_URL}/ingest/audio",
        files=files,
        data=data
    )
    r.raise_for_status()
    return r.json()


# 2️⃣ Trigger processing
def process_call(call_id):
    r = requests.post(f"{BASE_URL}/ingest/process/{call_id}")
    r.raise_for_status()
    return r.json()


# 3️⃣ Dashboard summary
def get_dashboard_summary():
    r = requests.get(f"{BASE_URL}/dashboard/summary?days=30")
    r.raise_for_status()
    return r.json()


# 4️⃣ Get alerts
def get_alerts():
    r = requests.get(f"{BASE_URL}/alerts?risk=CRITICAL&days=7")
    r.raise_for_status()
    return r.json()


# 5️⃣ Call details
def get_call_details(call_id):
    r = requests.get(f"{BASE_URL}/calls/{call_id}")
    r.raise_for_status()
    return r.json()


# 6️⃣ Add supervisor note
def add_note(call_id):
    payload = {
        "note": "Reviewed call. Coach agent on verification protocol."
    }
    r = requests.post(
        f"{BASE_URL}/calls/{call_id}/notes",
        json=payload
    )
    r.raise_for_status()
    return r.json()


# 7️⃣ Acknowledge alert
def acknowledge_alert(alert_id):
    r = requests.post(f"{BASE_URL}/alerts/{alert_id}/acknowledge")
    r.raise_for_status()
    return r.json()


# 🔁 FULL FLOW
def run_full_flow():
    # Upload
    upload_resp = upload_audio()
    pretty("UPLOAD RESPONSE", upload_resp)

    call_id = upload_resp["call_id"]

    # Process
    process_resp = process_call(call_id)
    pretty("PROCESS RESPONSE", process_resp)

    # Wait for processing (simple sleep for now)
    print("\n⏳ Waiting for processing...")
    time.sleep(5)

    # Dashboard
    summary = get_dashboard_summary()
    pretty("DASHBOARD SUMMARY", summary)

    # Alerts
    alerts = get_alerts()
    pretty("ALERTS", alerts)

    if alerts:
        alert_id = alerts[0]["alert_id"]

        # Call details
        call = get_call_details(call_id)
        pretty("CALL DETAILS", call)

        # Note
        note_resp = add_note(call_id)
        pretty("ADD NOTE", note_resp)

        # Ack alert
        ack_resp = acknowledge_alert(alert_id)
        pretty("ACK ALERT", ack_resp)


if __name__ == "__main__":
    run_full_flow()
