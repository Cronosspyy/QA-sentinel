import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

# ----------------------------
# Phase keyword heuristics (v1)
# ----------------------------
OPENING_KWS = ["hello", "hi", "good morning", "good evening", "battery smart", "support"]
VERIFY_KWS = ["verify", "verification", "registered", "mobile number", "otp", "id", "account", "dob", "date of birth"]
CLOSING_KWS = ["anything else", "further assistance", "thank you for calling", "have a nice day", "bye", "goodbye"]
RESOLUTION_KWS = ["restart", "reset", "reinstall", "swap", "battery", "ticket", "escalate", "complaint", "raise", "update"]
ISSUE_KWS = ["problem", "issue", "not working", "failed", "unable", "error", "stuck"]

DEFAULT_PHASES_ORDER = ["OPENING", "VERIFICATION", "ISSUE_IDENTIFICATION", "RESOLUTION", "CLOSING"]


def _to_float(x):
    try:
        return float(x)
    except:
        return None


def _sec_to_mmss(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def load_aws_transcribe_json(json_path: str) -> Dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_speaker_segments(transcribe_json: Dict) -> List[Dict[str, Any]]:
    """
    Extract speaker segments like:
    [{"speaker":"spk_0","start":0.23,"end":5.12}, ...]
    """
    speaker_labels = transcribe_json.get("results", {}).get("speaker_labels", {})
    segments = speaker_labels.get("segments", [])
    out = []
    for seg in segments:
        out.append({
            "speaker": seg.get("speaker_label"),
            "start": _to_float(seg.get("start_time")),
            "end": _to_float(seg.get("end_time")),
        })
    return out


def build_items(transcribe_json: Dict) -> List[Dict[str, Any]]:
    """
    Extract words/items with timestamps.
    """
    return transcribe_json.get("results", {}).get("items", [])


def assign_speaker_to_item(item: Dict[str, Any], speaker_segments: List[Dict[str, Any]]) -> str:
    """
    Find which speaker segment contains the item timestamp.
    """
    if item.get("type") != "pronunciation":
        return None

    t = _to_float(item.get("start_time"))
    if t is None:
        return None

    for seg in speaker_segments:
        if seg["start"] is None or seg["end"] is None:
            continue
        if seg["start"] <= t <= seg["end"]:
            return seg["speaker"]

    return None


def build_word_stream(items: List[Dict], speaker_segments: List[Dict]) -> List[Dict[str, Any]]:
    """
    Convert AWS items -> list of words with speaker info.
    """
    words = []
    for item in items:
        if item.get("type") != "pronunciation":
            # punctuation etc.
            continue

        speaker = assign_speaker_to_item(item, speaker_segments)
        if speaker is None:
            continue

        alt = item.get("alternatives", [{}])[0]
        content = alt.get("content", "")

        words.append({
            "speaker": speaker,
            "start": _to_float(item.get("start_time")),
            "end": _to_float(item.get("end_time")),
            "word": content
        })
    return words


def normalize_speakers(words: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Heuristic mapping spk_0/spk_1 -> Agent/Customer.
    Rule: speaker who speaks first is Agent (usually true for support calls).
    """
    if not words:
        return {}

    first_spk = words[0]["speaker"]
    unique = list(dict.fromkeys([w["speaker"] for w in words]))

    mapping = {}
    if len(unique) == 1:
        mapping[unique[0]] = "Agent"
        return mapping

    # First speaker = Agent, other = Customer
    mapping[first_spk] = "Agent"
    for spk in unique:
        if spk != first_spk:
            mapping[spk] = "Customer"
    return mapping


def merge_words_into_turns(
    words: List[Dict[str, Any]],
    speaker_map: Dict[str, str],
    max_gap_sec: float = 1.2
) -> List[Dict[str, Any]]:
    """
    Merge consecutive words into "turns" based on same speaker and small time gaps.
    """
    turns = []
    if not words:
        return turns

    current = {
        "turn_id": 1,
        "speaker": speaker_map.get(words[0]["speaker"], words[0]["speaker"]),
        "start": words[0]["start"],
        "end": words[0]["end"],
        "text": words[0]["word"]
    }

    for w in words[1:]:
        spk = speaker_map.get(w["speaker"], w["speaker"])
        gap = (w["start"] - current["end"]) if w["start"] is not None and current["end"] is not None else 0

        if spk == current["speaker"] and gap <= max_gap_sec:
            # continue same turn
            current["text"] += " " + w["word"]
            current["end"] = w["end"]
        else:
            turns.append(current)
            current = {
                "turn_id": len(turns) + 1,
                "speaker": spk,
                "start": w["start"],
                "end": w["end"],
                "text": w["word"]
            }

    turns.append(current)

    # add silence_after field
    for i in range(len(turns) - 1):
        gap = (turns[i + 1]["start"] - turns[i]["end"]) if turns[i]["end"] is not None and turns[i + 1]["start"] is not None else 0
        turns[i]["silence_after"] = round(max(gap, 0), 2)

    turns[-1]["silence_after"] = 0.0
    return turns


def detect_phase_for_turn(text: str) -> str:
    """
    Single turn phase guess using keywords.
    """
    t = text.lower()

    if any(k in t for k in CLOSING_KWS):
        return "CLOSING"
    if any(k in t for k in VERIFY_KWS):
        return "VERIFICATION"
    if any(k in t for k in OPENING_KWS):
        return "OPENING"
    if any(k in t for k in ISSUE_KWS):
        return "ISSUE_IDENTIFICATION"
    if any(k in t for k in RESOLUTION_KWS):
        return "RESOLUTION"

    # fallback
    return "RESOLUTION"


def apply_phase_order_constraint(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enforce mostly forward-only phase movement to reduce random flips.
    """
    phase_idx = {p: i for i, p in enumerate(DEFAULT_PHASES_ORDER)}
    current_idx = 0

    for t in turns:
        predicted = detect_phase_for_turn(t["text"])
        idx = phase_idx.get(predicted, current_idx)

        # Do not go backward too much:
        if idx < current_idx:
            predicted = DEFAULT_PHASES_ORDER[current_idx]
        else:
            current_idx = idx

        t["phase"] = predicted

    return turns


def count_interruptions(turns: List[Dict[str, Any]], threshold_gap=0.2) -> int:
    """
    Basic interruption detection:
    if speaker changes with near-zero gap, count as interruption.
    """
    count = 0
    for i in range(len(turns) - 1):
        if turns[i]["speaker"] != turns[i + 1]["speaker"]:
            gap = turns[i].get("silence_after", 0)
            if gap <= threshold_gap:
                count += 1
    return count


def structure_transcript(aws_json_path: str) -> Dict[str, Any]:
    """
    Main function: AWS JSON -> structured conversation dict
    """
    transcribe_json = load_aws_transcribe_json(aws_json_path)

    speaker_segments = build_speaker_segments(transcribe_json)
    items = build_items(transcribe_json)
    word_stream = build_word_stream(items, speaker_segments)

    speaker_map_raw = normalize_speakers(word_stream)
    turns = merge_words_into_turns(word_stream, speaker_map_raw)
    turns = apply_phase_order_constraint(turns)

    interruptions = count_interruptions(turns)

    call_id = Path(aws_json_path).stem

    output = {
        "call_id": call_id,
        "source": "aws_transcribe",
        "speaker_map": speaker_map_raw,
        "summary": {
            "num_turns": len(turns),
            "interruptions": interruptions,
            "duration_sec": turns[-1]["end"] if turns else 0
        },
        "turns": turns
    }
    return output


def process_transcripts_folder(input_dir: str, output_dir: str):
    """
    Batch mode: process all AWS JSON transcripts in a folder.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".json"]
    if not json_files:
        print(f"❌ No JSON files found in {input_dir}")
        return

    print(f"✅ Found {len(json_files)} AWS transcript JSONs")

    for jf in json_files:
        try:
            structured = structure_transcript(str(jf))
            out_path = output_dir / f"{structured['call_id']}_structured.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(structured, f, ensure_ascii=False, indent=2)
            print(f"✅ Structured saved: {out_path}")
        except Exception as e:
            print(f"❌ Failed on {jf.name}: {e}")
