# stt.py
import os
import uuid
import json
import subprocess
from faster_whisper import WhisperModel


MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")  # tiny/base/small/medium/large-v3
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")       # cpu / cuda
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE", "int8")  # int8 for cpu, float16 for cuda

_whisper_model = None


def get_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _whisper_model


def preprocess_audio(input_path: str, output_path: str):
    """
    Convert audio to 16khz mono wav (best for Whisper)
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def transcribe_audio(audio_path: str, call_id: str, result_path: str):
    """
    Transcribes audio and writes structured transcript JSON.
    """
    model = get_model()

    tmp_wav = f"/tmp/{uuid.uuid4().hex}.wav"
    preprocess_audio(audio_path, tmp_wav)

    segments, info = model.transcribe(
        tmp_wav,
        beam_size=5,
        vad_filter=True,
        language=None  # auto-detect
    )

    turns = []
    full_text_parts = []

    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        turns.append({
            "speaker": "unknown",  # diarization later
            "start": float(seg.start),
            "end": float(seg.end),
            "text": text
        })
        full_text_parts.append(text)

    result = {
        "call_id": call_id,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration_sec": info.duration,
        "turns": turns,
        "full_text": " ".join(full_text_parts)
    }

    os.remove(tmp_wav)

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
