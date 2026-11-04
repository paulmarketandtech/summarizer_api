import os

from dotenv import load_dotenv

load_dotenv()

transcripts_archive_path = os.getenv("ARCHIVE_TRANSCRIPT_PATH")
summaries_archive_path = os.getenv("ARCHIVE_SUMMARIES_PATH")


def save_transcript(yt_metadata) -> None:
    with open(
        f"{transcripts_archive_path}/{yt_metadata['transcript_file_name']}", "w"
    ) as file:
        file.write(yt_metadata["transcript_text"])


def save_summary(final_report_metadata) -> None:
    with open(
        f"{summaries_archive_path}/{final_report_metadata['summary_file_name']}", "w"
    ) as file:
        file.write(final_report_metadata["final_report"])


def file_manager(yt_metadata: dict, final_report_metadata: dict):

    save_transcript(yt_metadata)
    save_summary(final_report_metadata)
