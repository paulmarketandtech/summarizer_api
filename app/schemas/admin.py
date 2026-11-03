from pydantic import BaseModel, HttpUrl


class VideoSubmission(BaseModel):
    url: HttpUrl
    video_type: str  # "stocks", "macro", "drama_queen", etc.
