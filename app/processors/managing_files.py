import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "/app/archive"))
TRANSCRIPTS_ARCHIVE = ARCHIVE_DIR / "transcripts"
TRANSCRIPTS_ARCHIVE.mkdir(parents=True, exist_ok=True)
SUMMARIES_ARCHIVE = ARCHIVE_DIR / "summaries"
SUMMARIES_ARCHIVE.mkdir(parents=True, exist_ok=True)


def save_transcript(yt_metadata) -> None:
    with open(
        f"{TRANSCRIPTS_ARCHIVE}/{yt_metadata['transcript_file_name']}", "w"
    ) as file:
        file.write(yt_metadata["transcript_text"])


def save_summary(final_report_metadata) -> None:
    with open(
        f"{SUMMARIES_ARCHIVE}/{final_report_metadata['summary_file_name']}", "w"
    ) as file:
        file.write(final_report_metadata["final_report"])


def file_manager(yt_metadata: dict, final_report_metadata: dict):

    save_transcript(yt_metadata)
    save_summary(final_report_metadata)
