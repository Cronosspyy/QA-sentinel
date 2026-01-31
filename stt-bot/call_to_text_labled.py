import os
import json
import subprocess
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

# -----------------------------
# SETTINGS
# -----------------------------
AUDIO_FILE = "call.mp3"        # input call recording
OUTPUT_JSON = "transcript.json"

WHISPER_MODEL = "small"        # tiny/base/small/medium/large-v3
DEVICE = "cpu"                 # "cuda" if GPU
COMPUTE_TYPE = "int8"          # int8 for cpu, float16 for cuda

# HuggingFace token required for pyannote diarization
HF_TOKEN = "YOUR_HF_TOKEN_HERE"


def preprocess_audio(input_path, output_path="processed.wav"):
    """
    Convert audio -> 16kHz mono wav
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_path


def diarize_audio(wav_path):
    """
    Returns diarization segments: who spoke when
    """
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=HF_TOKEN)
    diarization = pipeline(wav_path)

    diar_segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        diar_segments.append({
            "speaker": speaker,
            "start": float(turn.start),
            "end": float(turn.end)
        })

    return diar_segments


def transcribe_audio(wav_path):
    """
    Returns whisper transcript segments (start/end/text)
    """
    model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)

    segments, info = model.transcribe(
        wav_path,
        beam_size=5,
        vad_filter=True
    )

    whisper_segments = []
    for seg in segments:
        whisper_segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip()
        })

    return whisper_segments, info.language


def assign_speaker(whisper_segments, diar_segments):
    """
    Assign each whisper segment to a speaker based on max overlap.
    """
    def overlap(a_start, a_end, b_start, b_end):
        return max(0.0, min(a_end, b_end) - max(a_start, b_start))

    labeled = []
    for seg in whisper_segments:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0

        for d in diar_segments:
            ov = overlap(seg["start"], seg["end"], d["start"], d["end"])
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = d["speaker"]

        labeled.append({
            "speaker": best_speaker,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })

    return labeled


def map_speakers_to_agent_customer(labeled_segments):
    """
    Since diarization gives generic SPEAKER_00, SPEAKER_01,
    we map them to AGENT/CUSTOMER heuristically:
    First speaker = AGENT, second = CUSTOMER.
    """
    speaker_ids = []
    for seg in labeled_segments:
        if seg["speaker"] not in speaker_ids and seg["speaker"] != "UNKNOWN":
            speaker_ids.append(seg["speaker"])

    mapping = {}
    if len(speaker_ids) >= 1:
        mapping[speaker_ids[0]] = "AGENT"
    if len(speaker_ids) >= 2:
        mapping[speaker_ids[1]] = "CUSTOMER"

    for seg in labeled_segments:
        seg["speaker"] = mapping.get(seg["speaker"], seg["speaker"])

    return labeled_segments


def main():
    wav = preprocess_audio(AUDIO_FILE)

    print("Running diarization...")
    diar_segments = diarize_audio(wav)

    print("Running transcription...")
    whisper_segments, language = transcribe_audio(wav)

    print("Merging results...")
    labeled_segments = assign_speaker(whisper_segments, diar_segments)
    labeled_segments = map_speakers_to_agent_customer(labeled_segments)

    output = {
        "call_file": AUDIO_FILE,
        "language": language,
        "segments": labeled_segments
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! Transcript saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
