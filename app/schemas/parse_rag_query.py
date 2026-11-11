from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.public import RagResult


class ParsedRagQuery(BaseModel):
    is_market_related: bool

    category: Literal[
        "company",
        "macro",
        "market",
        "comparison",
        "unrelated",
    ]

    # Empty for macro questions such as inflation, rates, recession, etc.
    companies: list[str] = Field(default_factory=list)

    topics: list[str] = Field(default_factory=list)

    embedding_query: str = ""

    video_year: int | None = None
    video_quarter: Literal[1, 2, 3, 4] | None = None

    mentioned_year: int | None = None
    mentioned_quarter: Literal[1, 2, 3, 4] | None = None

    @property
    def is_searchable(self) -> bool:
        return self.scope != "unrelated"


@dataclass(frozen=True)
class RagSearchConfig:
    top_k: int = 5
    min_similarity: float = 0.6

    # Useful for testing whether Qwen's rewritten query
    # actually improves retrieval.
    use_llm_rewritten_query: bool = True


class RetrievalFilters(BaseModel):
    companies: list[str] = Field(default_factory=list)

    # published_from: date | None = None
    # published_to: date | None = None


class RagSearchResponse(BaseModel):
    query: str
    is_market_related: bool

    message: str | None = None

    # Keep these while you are testing search behavior.
    parsed_query: ParsedRagQuery | None = None
    retrieval_query: str | None = None
    filters: RetrievalFilters | None = None

    results: list[RagResult] = Field(default_factory=list)


@dataclass
class SearchContext:
    user_query: str
    config: RagSearchConfig

    parsed_query: ParsedRagQuery | None = None
    retrieval_query: str | None = None
    filters: RetrievalFilters = field(default_factory=RetrievalFilters)

    results: list[dict[str, Any]] = field(default_factory=list)
    message: str | None = None

    stop: bool = False
