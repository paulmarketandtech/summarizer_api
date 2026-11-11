import os
from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Literal

from dotenv import load_dotenv

from app.schemas.parse_rag_query import ParsedRagQuery
from app.services.embeddings import EmbeddingService
from app.services.query_parser import QueryParser
from app.services.rag_filter import SearchHit, rag

load_dotenv()


ollama_host = os.getenv("OLLAMA_HOST")
parser = QueryParser(ollama_host=ollama_host)
embedder = EmbeddingService()


@dataclass
class QueryContext:
    raw_query: str
    top_k: int = 5

    # filled in by stages
    # parsed: ParsedQuery | None = None
    parsed: ParsedRagQuery | None = None
    query_vector: list[float] | None = None
    hits: list[SearchHit] = field(default_factory=list)

    # terminal state
    status: Literal["ok", "off_topic", "no_results"] = "ok"
    message: str | None = None

    # scratch space for experiments + timings
    debug: dict[str, Any] = field(default_factory=dict)

    def halt(self, status: str, message: str) -> None:
        self.status = status
        self.message = message

    @property
    def halted(self) -> bool:
        return self.status != "ok"


QueryStageFn = Callable[[QueryContext], None]


@dataclass
class QueryStage:
    name: str
    fn: QueryStageFn


class QueryPipeline:
    def __init__(self, name: str, stages: list[QueryStage]):
        self.name = name
        self.stages = stages

    def run(self, ctx: QueryContext) -> QueryContext:
        timings = {}
        for stage in self.stages:
            t0 = perf_counter()
            stage.fn(ctx)
            timings[stage.name] = round((perf_counter() - t0) * 1000)
            if ctx.halted:
                break
        ctx.debug["timings_ms"] = timings
        ctx.debug["pipeline"] = self.name
        return ctx


def stage_parse(ctx: QueryContext) -> None:
    ctx.parsed = parser.parse(ctx.raw_query)


def stage_gate(ctx: QueryContext) -> None:
    if not ctx.parsed.is_searchable:
        ctx.halt("off_topic", "I only cover stock-market videos.")


# TODO:this returns pure vector - don't understand the purpose of this
# TODO: so maybe rag_filter/RagService won't be used?
def stage_embed_query(ctx: QueryContext) -> None:
    ctx.query_vector = embedder.embed_text_sync(ctx.parsed.embedding_query)


def stage_retrieve(ctx: QueryContext) -> None:
    # over-fetch; later stages will cut it down
    ctx.hits = rag.raw_search(
        vector=ctx.query_vector,
        parsed=ctx.parsed,
        limit=ctx.top_k * 4,
    )
    ctx.debug["retrieved"] = len(ctx.hits)


def stage_threshold(ctx: QueryContext) -> None:
    before = len(ctx.hits)
    ctx.hits = [h for h in ctx.hits if h.similarity >= MIN_SIMILARITY]
    ctx.debug["dropped_by_threshold"] = before - len(ctx.hits)


def stage_dedup(ctx: QueryContext) -> None:
    seen: dict[str, int] = {}
    out = []
    for h in sorted(ctx.hits, key=lambda h: h.similarity, reverse=True):
        n = seen.get(h.video_id, 0)
        if n >= PER_VIDEO_CAP:
            continue
        seen[h.video_id] = n + 1
        out.append(h)
    ctx.hits = out


def stage_trim(ctx: QueryContext) -> None:
    ctx.hits = ctx.hits[: ctx.top_k]
    if not ctx.hits:
        ctx.halt("no_results", "Nothing in the indexed videos covers that.")
