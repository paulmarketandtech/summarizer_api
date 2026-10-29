"""
admin provides url
check if url already processed
download transcript
chunk it

do next:
add info extractor and save it to json

"""

from pathlib import Path

from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.services.lang_chunker import text_chunker

url = "https://www.youtube.com/watch?v=zBlSEABSHYs"
filepath = "../scratchpad/transcripts/"

fetcher = FileTranscriptFetcher(Path(filepath))
file_metadata = fetcher.fetch("yt_2025-12-17_couchinvestor_q7YZQgxswZ0_transcript")

transcript_text = file_metadata["transcript_text"]

chunks_metadata = text_chunker(transcript_text, 4000, 600)

transcript_char_length = file_metadata["transcript_char_length"]
print(transcript_char_length)
print(len(chunks_metadata))
print(chunks_metadata[1]["text"])
