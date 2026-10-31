from pathlib import Path

from app.config import config
from app.extraction.temp_extraction import (
    aggregate_extracted_data,
    extract_facts_from_chunk,
    generate_stock_report,
)
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.services.lang_chunker import text_chunker


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

    def extracted_aggregation(self, extracted_data: list):
        grouped_stocks = aggregate_extracted_data(extracted_data)
        return grouped_stocks

    def create_final_report(self, grouped_stocks):

        detected_companies = list(grouped_stocks.keys())
        print(f"Companies Detected: {detected_companies}")

        print("\nGenerating final reports per company...\n")
        final_output = f"# Stock Analysis Report\n**Companies Found:** {', '.join(detected_companies)}\n\n---\n"

        for stock_name, stock_data in grouped_stocks.items():
            print(f"Synthesizing summary for: {stock_name}...")
            llm_stock_metadata = generate_stock_report(stock_name, stock_data)
            final_output += llm_stock_metadata["stock_full_text"] + "\n\n---\n"

        return final_output


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
grouped_stocks = processor.extracted_aggregation(all_extractions)
# __import__("pprint").pprint(grouped_stocks)

final_output = processor.create_final_report(grouped_stocks)
# __import__("pprint").pprint(final_output)
# print(final_output)
