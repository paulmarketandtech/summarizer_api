import re
from datetime import datetime

import yt_dlp  # pyright: ignore
from youtube_transcript_api import YouTubeTranscriptApi  # pyright: ignore


class YouTubeTranscriptFetcher:
    def __init__(self, transcript_api=None) -> None:
        self.transcript_api = transcript_api or YouTubeTranscriptApi()

    def get_video_info(self, url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "--cookies": "./www.youtube.com_cookies.txt",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore
            info = ydl.extract_info(url, download=False)

            upload_date_str = info.get("upload_date")  # YYYYMMDD format
            parsed_date = datetime.strptime(upload_date_str, "%Y%m%d").date()

            return {
                "title": info.get("title"),
                "uploader_id": info.get("uploader_id"),
                "published_date": parsed_date,
                "url": url,
            }

    def extract_youtube_id(self, url: str) -> str | None:
        """
        Extracts the YouTube video ID from various YouTube URL formats.

        Examples:
        - https://www.youtube.com/watch?v=zBlSEABSHYs           → zBlSEABSHYs
        - https://youtu.be/zBlSEABSHYs                          → zBlSEABSHYs
        - https://www.youtube.com/embed/zBlSEABSHYs             → zBlSEABSHYs
        - https://www.youtube.com/v/zBlSEABSHYs                 → zBlSEABSHYs
        - https://m.youtube.com/watch?v=zBlSEABSHYs&t=30s       → zBlSEABSHYs
        """
        pattern = re.compile(
            r"(?:https?://)?"
            r"(?:www\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)/"
            r"(?:watch\?v=|embed/|v/|.+/)?"
            r"([a-zA-Z0-9_-]{11})"
        )

        match = pattern.search(url)
        if match:
            return match.group(1)
        return None

    def fetch(self, url: str) -> dict:
        """Creates transcript of a given YT video
        Returns metadata from YT"""

        yt_id = self.extract_youtube_id(url)
        yt_metadata = self.get_video_info(url)
        fetched_transcript = self.transcript_api.fetch(
            yt_id, languages=["en", "pl", "de"]
        )
        transcript_text = ""

        for snippet in fetched_transcript:
            transcript_text += snippet.text
            transcript_text += " "

        channel_name_capitalized = "".join(
            word.capitalize() for word in yt_metadata["uploader_id"].split()
        )
        channel_name_clean = re.sub(r"[^a-zA-Z0-9\\s]", "", channel_name_capitalized)

        filename = f"yt_{yt_metadata['published_date']}_{channel_name_clean}_{yt_id}_transcript.txt"

        yt_metadata["transcript_file_name"] = filename
        yt_metadata["yt_id"] = yt_id
        yt_metadata["transcript_text"] = transcript_text
        yt_metadata["transcript_char_length"] = len(transcript_text)
        yt_metadata["transcript_word_count"] = len(transcript_text.split())

        return yt_metadata
