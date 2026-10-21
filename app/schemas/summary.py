from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# 1. Define the nested Summary schema (only what public can see)
class PublicSummaryOut(BaseModel):
    final_report: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 2. Define the main Video schema (flattens/nests the above)
class PublicVideoOut(BaseModel):
    # Video fields the user asked for
    id: UUID
    title: str | None
    url: str
    yt_creator: str | None
    published_date: date | None
    content_type: str | None
    summary_preview: str | None

    # Nest the summary so the frontend gets clean JSON
    summary: PublicSummaryOut | None

    model_config = ConfigDict(from_attributes=True)


class TitlesOut(BaseModel):
    titles: list[str]
