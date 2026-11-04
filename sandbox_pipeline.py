from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.config import config
from app.extraction.temp_extraction import (
    aggregate_extracted_data,
    extract_facts_from_chunk,
    generate_stock_report,
)
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.fetchers.youtube_fetcher import YouTubeTranscriptFetcher
from app.processors.db_population import (
    db_population_manager,
    update_full_processing_time,
)
from app.processors.managing_files import file_manager
from app.services.embeddings import EmbeddingService
from app.services.lang_chunker import text_chunker


class SourceKind(str, Enum):
    FILE = "file"
    URL = "url"


# ─── Config ────────────────────────────────────────────────────────────


@dataclass
class PipelineConfig:

    source_kind: SourceKind
    source: str
    is_url: bool = False
    chunk_size: int = 3500
    chunk_overlap: int = 700
    run_tag: str = "default"

    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768

    # behaviour switches
    persist: bool = False
    skip_if_exists: bool = True


@dataclass
class TranscriptData:
    video_id: str
    title: str | None
    channel: str | None
    published_at: datetime | None
    url: str | None
    transcript_text: str


# ─── Stage: just a named callable ──────────────────────────────────────


@dataclass
class Stage:
    name: str
    fn: Callable[[dict, PipelineConfig], Any]


# ─── The runner ────────────────────────────────────────────────────────
class Pipeline:
    """
    Executes stages in order.  Each stage receives:
        ctx  – a dict that accumulates results under stage names
        cfg  – the PipelineConfig for this run

    A stage returns whatever it wants; the runner stores it as ctx[stage.name].
    """

    def __init__(self, name: str, stages: list[Stage]):
        # self.name = name
        self.stages = stages

    def run(self, cfg: PipelineConfig, *, start_from: str | None = None) -> dict:
        ctx: dict[str, Any] = {}
        started = start_from is None

        for stage in self.stages:
            if not started:
                started = stage.name == start_from
                if not started:
                    continue

            print(f"▶ {stage.name}")
            ctx[stage.name] = stage.fn(ctx, cfg)

        return ctx


# ─── The stages (pure functions – easy to swap) ────────────────────────
from app.fetchers.youtube_fetcher import YouTubeTranscriptFetcher


def stage_fetch_transcript(ctx, cfg):
    fetcher = (
        YoutubeTranscriptFetcher()
        if cfg.is_url
        else FileTranscriptFetcher(config.TRANSCRIPTS_DIR)
    )
    return fetcher.fetch(cfg.source)


"""
probably to be deleted
def stage_fetch_transcript(ctx: dict, cfg: PipelineConfig) -> dict:
    if cfg.source_kind is SourceKind.FILE:
        return FileTranscriptFetcher(config.TRANSCRIPTS_DIR).fetch(cfg.source)
    return YoutubeTranscriptFetcher().fetch(cfg.source)


def stage_fetch_transcript_old(ctx: dict, cfg: PipelineConfig) -> dict:
    fetcher = FileTranscriptFetcher(config.TRANSCRIPTS_DIR)
    return fetcher.fetch(cfg.filename)
"""


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


def stage_embed(ctx, cfg):
    svc = EmbeddingService()
    p = ctx["process"]

    for chunk in ctx["chunk"]:
        chunk["embedding"] = svc.embed_text_sync(chunk["text"])

    for stock in p["llm_stocks_metadata"]:
        stock["embedding"] = svc.embed_text_sync(stock["stock_full_text"])

    p["report_metadata"]["embedding"] = svc.embed_text_sync(
        p["report_metadata"]["final_report"]
    )
    return True  # mutates in place, nothing to return


def stage_persist(ctx, cfg):
    p = ctx["process"]
    db_population_manager(
        ctx["fetch"],
        ctx["chunk"],
        p["llm_chunks_metadata"],
        p["llm_stocks_metadata"],
        p["report_metadata"],
    )


def stage_archive(ctx, cfg):
    file_manager(ctx["fetch"], ctx["process"]["report_metadata"])


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

# ctx = DEFAULT_PIPELINE.run(cfg)

# print(ctx["report"])
