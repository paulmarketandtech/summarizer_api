from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.config import config
from app.extraction.temp_extraction import (
    aggregate_extracted_data,
    extract_facts_from_chunk,
    generate_stock_report,
)

# ─── Existing building blocks (unchanged, just imported) ───────────────
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.services.lang_chunker import text_chunker

TRANSCRIPTS_DIR = config.TRANSCRIPTS_DIR


# ─── Config ────────────────────────────────────────────────────────────
@dataclass
class PipelineConfig:
    """One config per video-type experiment."""

    filename: str
    chunk_size: int = 3500
    chunk_overlap: int = 700
    # tag this run so you can tell results apart
    run_tag: str = "default"


# ─── Stage: just a named callable ──────────────────────────────────────
StageFn = Callable[[dict, PipelineConfig], Any]


@dataclass
class Stage:
    name: str
    fn: StageFn


# ─── The runner ────────────────────────────────────────────────────────
class Pipeline:
    """
    Executes stages in order.  Each stage receives:
        ctx  – a dict that accumulates results under stage names
        cfg  – the PipelineConfig for this run

    A stage returns whatever it wants; the runner stores it as ctx[stage.name].
    """

    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, cfg: PipelineConfig, *, start_from: str | None = None) -> dict:
        ctx: dict[str, Any] = {}
        started = start_from is None

        for stage in self.stages:
            if not started:
                if stage.name == start_from:
                    started = True
                else:
                    continue

            print(f"▶ {stage.name}")
            ctx[stage.name] = stage.fn(ctx, cfg)

        return ctx


# ─── The stages (pure functions – easy to swap) ────────────────────────
def stage_fetch_transcript(ctx: dict, cfg: PipelineConfig) -> dict:
    fetcher = FileTranscriptFetcher(TRANSCRIPTS_DIR)
    return fetcher.fetch(cfg.filename)


def stage_chunk(ctx: dict, cfg: PipelineConfig) -> list[dict]:
    return text_chunker(
        raw_transcript=ctx["fetch_transcript"]["transcript_text"],
        max_chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
    )


def stage_extract_facts(ctx: dict, cfg: PipelineConfig) -> list[dict]:
    results = []
    for i, chunk in enumerate(ctx["chunk"]):
        extracted, _meta = extract_facts_from_chunk(chunk["text"])
        results.append(extracted)
    return results


def stage_aggregate(ctx: dict, cfg: PipelineConfig) -> dict:
    return aggregate_extracted_data(ctx["extract_facts"])


def stage_report(ctx: dict, cfg: PipelineConfig) -> str:
    grouped = ctx["aggregate"]
    companies = list(grouped.keys())
    print(f"Companies: {companies}")

    parts = [f"# Stock Analysis Report\n**Companies:** {', '.join(companies)}\n\n---\n"]
    for name, data in grouped.items():
        print(f"  synthesising {name}…")
        parts.append(generate_stock_report(name, data)["stock_full_text"])
        parts.append("\n---\n")

    return "\n".join(parts)


# ─── Assemble the default pipeline ─────────────────────────────────────
DEFAULT_PIPELINE = Pipeline(
    [
        Stage("fetch_transcript", stage_fetch_transcript),
        Stage("chunk", stage_chunk),
        Stage("extract_facts", stage_extract_facts),
        Stage("aggregate", stage_aggregate),
        Stage("report", stage_report),
    ]
)

# run it
cfg = PipelineConfig(
    filename="yt_2026-08-10_josephcarlsonafterhours_TA6rz8gLQxI_transcript.txt",
    run_tag="stock_strict_v3",
)

ctx = DEFAULT_PIPELINE.run(cfg)

print(ctx["report"])
