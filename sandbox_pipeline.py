from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import config
from app.extraction.temp_extraction import process_transcript
from app.fetchers.file_fetcher import FileTranscriptFetcher
from app.fetchers.youtube_fetcher import YouTubeTranscriptFetcher
from app.processors.db_population import (
    db_population_manager,
    update_full_processing_time,
)
from app.processors.managing_files import file_manager
from app.services.embeddings import EmbeddingService
from app.services.lang_chunker import text_chunker
from app.utils.check_video_processed import check_id_in_db, get_processed_summary
from app.utils.create_report_metadata import create_final_report_metadata

# ─── Config ────────────────────────────────────────────────────────────


@dataclass
class PipelineConfig:

    source: str
    is_url: bool = False
    chunk_size: int = 3000
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


def stage_fetch_transcript(ctx: dict, cfg: PipelineConfig) -> dict:

    fetcher = (
        YouTubeTranscriptFetcher()
        if cfg.is_url
        else FileTranscriptFetcher(config.TRANSCRIPTS_DIR)
    )
    return fetcher.fetch(cfg.source)


def stage_chunk(ctx: dict, cfg: PipelineConfig) -> list[dict]:
    return text_chunker(
        raw_transcript=ctx["fetch_transcript"]["transcript_text"],
        max_chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
    )


"""
# tweak report prompt, rerun just that part — fetch/chunk already in ctx
# (note: start_from="process" redoes extraction too, since they're one stage.
#  Split stage_process in two later if that gets annoying.)
# Those 3 funcs could go instead of stage_process
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
"""


def stage_process(ctx: dict, cfg: PipelineConfig) -> dict:
    final_report, llm_chunks_metadata, llm_stocks_metadata = process_transcript(
        ctx["chunk"]
    )
    report_metadata = create_final_report_metadata(
        final_report, ctx["fetch_transcript"]["transcript_file_name"]
    )
    return {
        "final_report": final_report,
        "llm_chunks_metadata": llm_chunks_metadata,
        "llm_stocks_metadata": llm_stocks_metadata,
        "report_metadata": report_metadata,
    }


def stage_embed(ctx: dict, cfg: PipelineConfig):
    svc = EmbeddingService()
    p = ctx["process"]

    for chunk in ctx["chunk"]:
        chunk["embedding"] = svc.embed_text_sync(chunk["text"])

    for stock in p["llm_stocks_metadata"]:
        stock["embedding"] = svc.embed_text_sync(stock["stock_full_text"])

    p["report_metadata"]["embedding"] = svc.embed_text_sync(
        p["report_metadata"]["final_report"]
    )


def stage_persist(ctx: dict, cfg: PipelineConfig):
    p = ctx["process"]
    db_population_manager(
        ctx["fetch_transcript"],
        ctx["chunk"],
        p["llm_chunks_metadata"],
        p["llm_stocks_metadata"],
        p["report_metadata"],
    )


def stage_archive(ctx: dict, cfg: PipelineConfig):
    file_manager(ctx["fetch_transcript"], ctx["process"]["report_metadata"])


# ─── Assemble the default pipeline ─────────────────────────────────────

CORE = [
    Stage("fetch_transcript", stage_fetch_transcript),
    Stage("chunk", stage_chunk),
    Stage("process", stage_process),
]

SANDBOX = Pipeline("sandbox", CORE)

PROD = Pipeline(
    "prod",
    CORE
    + [
        Stage("embed", stage_embed),
        Stage("persist", stage_persist),
        Stage("archive", stage_archive),
    ],
)

PIPELINES = {"sandbox": SANDBOX, "prod": PROD}


def get_pipeline() -> Pipeline:
    name = os.getenv("APP_MODE") or ("sandbox" if config.MODE == "sandbox" else "prod")
    return PIPELINES[name]


# filename = "yt_2026-08-10_josephcarlsonafterhours_TA6rz8gLQxI_transcript.txt"
# filename = "yt_2026-11-04_futurumequities_tmTJc5HfyBE_transcript.txt"
# url = "https://youtu.be/tmTJc5HfyBE"


# prod
if os.getenv("APP_MODE") == "prod":
    print("I'm in PROD!!")
    video_processed, yt_id = check_id_in_db(url)
    if video_processed:
        print("Video was already processed. Here you are!")
        processed_title, processed_summary = get_processed_summary(yt_id)
        print(f"{processed_title}\n---\n{processed_summary}")
    else:
        print("processing a new video on PROD")
        start_time = time.perf_counter()
        cfg = PipelineConfig(source=url, is_url=True, run_tag="strict_v3")
        ctx = get_pipeline().run(cfg)
        print(ctx["process"]["final_report"])
        processing_time = time.perf_counter() - start_time
        update_full_processing_time(processing_time, yt_id)
        print(processing_time)
# sandbox
else:
    print("I'm in DEV!!")
    cfg = PipelineConfig(source=filename, run_tag="strict_v3")
    ctx = get_pipeline().run(cfg)
    print(ctx["process"]["final_report"])
