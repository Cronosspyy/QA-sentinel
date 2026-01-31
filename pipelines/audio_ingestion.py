import os
import time
import boto3
import requests
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# =========================
# LOAD ENV
# =========================
load_dotenv()

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}

# =========================
# AWS CLIENT FACTORY
# =========================

def get_aws_clients():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    transcribe = boto3.client("transcribe", region_name=AWS_REGION)
    return s3, transcribe

# =========================
# CORE FUNCTIONS
# =========================

def list_audio_files(directory: str):
    directory = Path(directory)
    return [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]


def upload_to_s3(s3_client, file_path: Path, bucket: str):
    s3_key = f"audio/{file_path.name}"
    s3_client.upload_file(str(file_path), bucket, s3_key)
    return f"s3://{bucket}/{s3_key}"


def start_transcription(transcribe_client, media_uri: str, job_prefix: str):
    job_name = f"{job_prefix}-{int(time.time())}"

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat=media_uri.split(".")[-1],
        LanguageCode="en-IN",
        Settings={
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": 2
        }
    )
    return job_name


def wait_for_transcription(transcribe_client, job_name: str, poll_interval=15):
    while True:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        status = response["TranscriptionJob"]["TranscriptionJobStatus"]

        print(f"⏳ {job_name} → {status}")

        if status in ["COMPLETED", "FAILED"]:
            return response

        time.sleep(poll_interval)


def download_transcript(transcript_url: str, save_path: str):
    response = requests.get(transcript_url)
    response.raise_for_status()

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(response.text)

# =========================
# PIPELINE (THIS IS WHAT YOU CALL)
# =========================

def process_audio_directory(
    input_dir: str,
    s3_bucket: str,
    output_dir: str
):
    os.makedirs(output_dir, exist_ok=True)

    s3_client, transcribe_client = get_aws_clients()
    audio_files = list_audio_files(input_dir)

    if not audio_files:
        print("❌ No audio files found.")
        return

    print(f"🎧 Found {len(audio_files)} audio files in {input_dir}")

    for audio_file in audio_files:
        print(f"\n🔹 Processing: {audio_file.name}")

        try:
            # 1. Upload
            s3_uri = upload_to_s3(
                s3_client,
                audio_file,
                s3_bucket
            )
            print(f"⬆ Uploaded to {s3_uri}")

            # 2. Transcribe
            job_name = start_transcription(
                transcribe_client,
                media_uri=s3_uri,
                job_prefix=audio_file.stem
            )
            print(f"📝 Transcription job started: {job_name}")

            # 3. Wait
            result = wait_for_transcription(
                transcribe_client,
                job_name
            )

            if result["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
                print(f"❌ Transcription failed for {audio_file.name}")
                continue

            # 4. Download
            transcript_url = result["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            output_path = os.path.join(
                output_dir,
                f"{job_name}.json"
            )

            download_transcript(
                transcript_url,
                output_path
            )
            print(f"✅ Transcript saved → {output_path}")

        except ClientError as e:
            print(f"❌ AWS error for {audio_file.name}: {e}")

        except Exception as e:
            print(f"❌ Unexpected error for {audio_file.name}: {e}")
