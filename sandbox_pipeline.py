"""
set local transcript file
chunk it

do next:
add info extractor and save it to json

"""

from pathlib import Path

from app.config import config
from app.extraction.temp_extraction import extract_facts_from_chunk
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.services.lang_chunker import text_chunker

TRANSCRIPTS_DIR = config.TRANSCRIPTS_DIR
filename = "yt_2025-12-17_couchinvestor_q7YZQgxswZ0_transcript.txt"


class ProcessTranscriptLocal:
    def __init__(
        self,
        transcript_dir: Path,
        filename: str,
        max_chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.transcript_dir = transcript_dir
        self.filename = filename
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def get_transcript_data(self):
        fetcher = FileTranscriptFetcher(self.transcript_dir)
        file_metadata = fetcher.fetch(self.filename)
        return file_metadata

    def chunker(self):
        file_metadata = self.get_transcript_data()
        raw_text = file_metadata["transcript_text"]
        chunks_metadata = text_chunker(
            raw_text, self.max_chunk_size, self.chunk_overlap
        )
        return chunks_metadata

    def fact_extraction(self):
        chunks = self.chunker()
        extracted_facts = []
        for chunk in chunks:
            extracted_facts.append(extract_facts_from_chunk(chunk["text"]))

        return extracted_facts


# processor = ProcessTranscriptLocal(TRANSCRIPTS_DIR, filename, 4000, 800)

# print(processor.fact_extraction())

"""
chunks_metadata = text_chunker(transcript_text, 4000, 600)

transcript_char_length = file_metadata["transcript_char_length"]
print(transcript_char_length)
print(len(chunks_metadata))
print(chunks_metadata[1]["text"])
"""
