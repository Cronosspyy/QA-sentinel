from pipelines.audio_ingestion import process_audio_directory

if __name__ == "__main__":
    process_audio_directory(
        input_dir="data/audio",
        s3_bucket="qa-call-audio",
        output_dir="transcripts/aws_raw"
    )
