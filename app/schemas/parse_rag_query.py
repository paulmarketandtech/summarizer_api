from typing import Literal

from pydantic import BaseModel, Field


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
