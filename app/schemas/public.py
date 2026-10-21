import uuid
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base class for schemas built from SQLAlchemy objects.

    from_attributes=True lets Pydantic read obj.title instead of obj["title"].
    """

    model_config = ConfigDict(from_attributes=True)


# ---------- Output schemas ----------


class SummaryPublic(ORMModel):
    final_report: str
    word_count: int | None = None
    created_at: datetime


class VideoPublicItem(ORMModel):
    """One row in search results. No full report, to keep the payload small."""

    id: uuid.UUID
    url: str
    title: str | None = None
    yt_creator: str | None = None
    published_date: date | None = None
    content_type: str | None = None
    summary_preview: str | None = None


class VideoPublicDetail(VideoPublicItem):
    """Single video page. Inherits everything above and adds the summary."""

    summary: SummaryPublic | None = None


class Page(BaseModel, Generic[T]):
    """Generic pagination wrapper: Page[VideoPublicItem], Page[SomethingElse], etc."""

    items: list[T]
    total: int
    limit: int
    offset: int


# ---------- Input schema ----------


class VideoSearchParams(BaseModel):
    """Query string parameters for GET /public/videos."""

    q: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
        description="Free text. Searches title, creator, content type, url, summary preview and full report.",
    )
    creator: str | None = Field(default=None, max_length=500)
    content_type: str | None = Field(default=None, max_length=100)
    published_after: date | None = None
    published_before: date | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_date_range(self):
        if (
            self.published_after
            and self.published_before
            and self.published_after > self.published_before
        ):
            raise ValueError("published_after must be on or before published_before")
        return self


# ---------- RAG schema ----------


class RagQuery(BaseModel):
    query: str


class RagResult(BaseModel):
    video_id: str
    text: str
    source: str
    similarity: float
