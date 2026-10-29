from datetime import date
from types import NoneType
from unittest.mock import MagicMock, patch

from app.fetchers.youtube_fetcher import YouTubeTranscriptFetcher

fetcher = YouTubeTranscriptFetcher()


@patch("app.fetchers.youtube_fetcher.yt_dlp.YoutubeDL")
def test_get_video_info_success(mock_yt_dlp_class):
    mock_instance = MagicMock()
    mock_yt_dlp_class.return_value.__enter__.return_value = mock_instance

    # Define what the fake YouTube extraction payload looks like
    mock_instance.extract_info.return_value = {
        "title": "Test AI Video 2026",
        "uploader_id": "ticker symbol you",
        "upload_date": "20261029",
    }

    fetcher = YouTubeTranscriptFetcher()
    result = fetcher.get_video_info("https://youtube.com")

    assert result["title"] == "Test AI Video 2026"
    assert result["published_date"] == date(2026, 10, 29)
    assert result["uploader_id"] == "ticker symbol you"


@patch.object(YouTubeTranscriptFetcher, "get_video_info")
def test_fetch_orchestration_and_formatting(mock_get_video_info):
    # Arrange: Mock the internal get_video_info return so it doesn't call real yt_dlp
    mock_get_video_info.return_value = {
        "title": "These 3 AI Stocks Will Skyrocket In 2026",
        "uploader_id": "ticker symbol you",
        "published_date": date(2026, 10, 29),
        "url": "https://www.youtube.com/watch?v=zBlSEABSHYs",
    }

    # Arrange: Create a mock for the Transcript API snippets returning dummy iterable data
    mock_transcript_api = MagicMock()

    # Simulate the snippet objects returned by the real API (.text attribute)
    mock_snippet_1 = MagicMock()
    mock_snippet_1.text = (
        "the key to finding great stocks is understanding a company's products"
    )
    mock_snippet_2 = MagicMock()
    mock_snippet_2.text = "not just their profits"

    mock_transcript_api.fetch.return_value = [mock_snippet_1, mock_snippet_2]

    fetcher = YouTubeTranscriptFetcher(transcript_api=mock_transcript_api)

    result = fetcher.fetch("https://www.youtube.com/watch?v=zBlSEABSHYs")

    assert result["yt_id"] == "zBlSEABSHYs"
    assert "understanding a company's products" in result["transcript_text"]
    assert (
        result["transcript_file_name"]
        == "yt_2026-10-29_TickerSymbolYou_zBlSEABSHYs_transcript.txt"
    )
    assert result["transcript_word_count"] == 15


good_urls = [
    "https://www.youtube.com/watch?v=zBlSEABSHYs",
    "https://youtu.be/zBlSEABSHYs",
]

bad_urls = [
    "https://x.com/StockSavvyShay/status/2115799552901124128",
    "https://www.youtube.com/v/zBl--SE++ABSHYsaaaaaaaa",
]


def test_good_id_extraction():
    yt_id = fetcher.extract_youtube_id(good_urls[0])
    assert isinstance(yt_id, str)


def test_bad_id_extraction():
    bad_yt_id = fetcher.extract_youtube_id(bad_urls[1])
    assert isinstance(bad_yt_id, NoneType)
