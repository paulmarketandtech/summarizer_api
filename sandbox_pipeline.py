"""
set local transcript file
chunk it

do next:
add info extractor and save it to json

"""

from pathlib import Path

from app.config import config
from app.extraction.temp_extraction import (
    aggregate_extracted_data,
    extract_facts_from_chunk,
)
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.services.lang_chunker import text_chunker

"""
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
"""


class ProcessTranscriptLocal:
    def __init__(self) -> None:
        pass

    def get_transcript_data(self, transcript_dir: Path, filename: str) -> dict:
        fetcher = FileTranscriptFetcher(transcript_dir)
        file_metadata = fetcher.fetch(filename)
        return file_metadata

    def chunker(self, raw_text, chunk_size, chunk_overlap) -> list:
        chunks_metadata = text_chunker(
            raw_transcript=raw_text,
            max_chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return chunks_metadata

    def fact_extraction(self, chunk_text) -> tuple[dict, dict]:
        extracted_data, llm_chunk_metadata = extract_facts_from_chunk(chunk_text)

        return extracted_data, llm_chunk_metadata

    def extracted_agggregation(self, extracted_data: list):
        grouped_stocks = aggregate_extracted_data(extracted_data)
        return grouped_stocks

    def create_final_report(self):
        # TODO: create a final report so it's easier to read the output
        ...


TRANSCRIPTS_DIR = config.TRANSCRIPTS_DIR
sofi_filename = "yt_2025-12-17_couchinvestor_q7YZQgxswZ0_transcript.txt"
filename = "yt_2026-08-10_josephcarlsonafterhours_TA6rz8gLQxI_transcript.txt"

processor = ProcessTranscriptLocal()
file_metadata = processor.get_transcript_data(TRANSCRIPTS_DIR, filename)
chunks_metadata = processor.chunker(file_metadata["transcript_text"], 3500, 700)

all_extractions = []
for chunk in chunks_metadata:
    extracted_data, llm_chunk_metadata = processor.fact_extraction(chunk["text"])
    all_extractions.append(extracted_data)

print("pipeline")
print("-" * 50)
grouped_data = processor.extracted_agggregation(all_extractions)
__import__("pprint").pprint(grouped_data)
detected_companies = list(grouped_data.keys())
print(f"Companies Detected: {detected_companies}")

"""
chunks_metadata = text_chunker(transcript_text, 4000, 600)

transcript_char_length = file_metadata["transcript_char_length"]
print(transcript_char_length)
print(len(chunks_metadata))
print(chunks_metadata[1]["text"])
"""
