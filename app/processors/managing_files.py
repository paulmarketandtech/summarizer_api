import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "archive"))
TRANSCRIPTS_ARCHIVE = ARCHIVE_DIR / "transcripts"
SUMMARIES_ARCHIVE = ARCHIVE_DIR / "summaries"


def write_archive(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def save_transcript(yt_metadata: dict) -> Path:
    return write_archive(
        TRANSCRIPTS_ARCHIVE / yt_metadata["transcript_file_name"],
        yt_metadata["transcript_text"],
    )


def save_summary(final_report_metadata: dict) -> Path:
    return write_archive(
        SUMMARIES_ARCHIVE / final_report_metadata["summary_file_name"],
        final_report_metadata["final_report"],
    )


def file_manager(yt_metadata: dict, final_report_metadata: dict) -> dict[str, Path]:
    return {
        "transcript": save_transcript(yt_metadata),
        "summary": save_summary(final_report_metadata),
    }
