# from pipelines.audio_ingestion import process_audio_directory

# if __name__ == "__main__":
#     process_audio_directory(
#         input_dir="data/audio",
#         s3_bucket="qa-call-audio",
#         output_dir="transcripts/aws_raw"
#     )
    

from pipelines.transcript_structurer import process_transcripts_folder

if __name__ == "__main__":
    process_transcripts_folder(
        input_dir="transcripts/aws_raw",
        output_dir="transcripts/parsed"
     )
