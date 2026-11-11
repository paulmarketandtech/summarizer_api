from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.parse_rag_query import (
    RagSearchConfig,
    RagSearchResponse,
    SearchContext,
)
from app.services.query_parser import QueryParser
from app.services.rag_filter import RagService
from app.utils.rag_date_conventer import quarter_to_date_range


@dataclass
class SearchServices:
    query_understanding: QueryParser
    rag_service: RagService


StageFn = Callable[[SearchContext, SearchServices], None]


@dataclass(frozen=True)
class SearchStage:
    name: str
    fn: StageFn


class RagSearchPipeline:
    def __init__(
        self,
        services: SearchServices,
        config: RagSearchConfig,
        stages: list[SearchStage],
    ):
        self.services = services
        self.config = config
        self.stages = stages

    def run(self, user_query: str) -> RagSearchResponse:
        ctx = SearchContext(
            user_query=user_query,
            config=self.config,
        )

        for stage in self.stages:
            print(f"▶ Search stage: {stage.name}")

            stage.fn(ctx, self.services)

            if ctx.stop:
                break

        return RagSearchResponse(
            query=ctx.user_query,
            is_market_related=(
                ctx.parsed_query.is_market_related
                if ctx.parsed_query is not None
                else False
            ),
            message=ctx.message,
            parsed_query=ctx.parsed_query,
            retrieval_query=ctx.retrieval_query,
            filters=ctx.filters,
            results=ctx.results,
        )


def stage_parse_query(
    ctx: SearchContext,
    services: SearchServices,
) -> None:
    ctx.parsed_query = services.query_understanding.parse(ctx.user_query)


def stage_reject_unrelated(
    ctx: SearchContext,
    services: SearchServices,
) -> None:
    assert ctx.parsed_query is not None

    if ctx.parsed_query.is_market_related:
        return

    ctx.message = (
        "I can only search indexed stock market, company, "
        "and macroeconomic video content."
    )
    ctx.stop = True


# Not in use right now
def stage_build_filters(
    ctx: SearchContext,
    services: SearchServices,
) -> None:
    assert ctx.parsed_query is not None

    ctx.filters.companies = ctx.parsed_query.companies

    if (
        ctx.parsed_query.video_year is not None
        and ctx.parsed_query.video_quarter is not None
    ):
        published_from, published_to = quarter_to_date_range(
            ctx.parsed_query.video_year,
            ctx.parsed_query.video_quarter,
        )

        ctx.filters.published_from = published_from
        ctx.filters.published_to = published_to


def stage_build_retrieval_query(
    ctx: SearchContext,
    services: SearchServices,
) -> None:
    assert ctx.parsed_query is not None

    if ctx.config.use_llm_rewritten_query and ctx.parsed_query.embedding_query:
        ctx.retrieval_query = ctx.parsed_query.embedding_query
    else:
        ctx.retrieval_query = ctx.user_query


def stage_retrieve(
    ctx: SearchContext,
    services: SearchServices,
) -> None:
    assert ctx.retrieval_query is not None

    ctx.results = services.rag_service.search(
        query=ctx.retrieval_query,
        top_k=ctx.config.top_k,
        min_similarity=ctx.config.min_similarity,
        # Use the argument names you added to your RagService.
        # company_names=ctx.filters.companies or None,
        # published_from=ctx.filters.published_from,
        # published_to=ctx.filters.published_to,
    )

    if not ctx.results:
        ctx.message = "No sufficiently relevant results were found."


DEFAULT_SEARCH_STAGES = [
    SearchStage("parse_query", stage_parse_query),
    SearchStage("reject_unrelated", stage_reject_unrelated),
    SearchStage("build_filters", stage_build_filters),
    SearchStage("build_retrieval_query", stage_build_retrieval_query),
    SearchStage("retrieve", stage_retrieve),
]

import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

ollama_host = os.getenv("OLLAMA_HOST")


def build_rag_search_pipeline(db: Session) -> RagSearchPipeline:
    query_understanding = QueryParser(ollama_host)

    services = SearchServices(
        query_understanding=query_understanding,
        rag_service=RagService(db),
    )

    config = RagSearchConfig(
        top_k=5,
        min_similarity=0.6,
        use_llm_rewritten_query=True,
    )

    return RagSearchPipeline(
        services=services,
        config=config,
        stages=DEFAULT_SEARCH_STAGES,
    )


"""
from app.storage.database import get_session

with get_session() as session:
    db = RagService(session)

pipeline = build_rag_search_pipeline(db=db)
"""
