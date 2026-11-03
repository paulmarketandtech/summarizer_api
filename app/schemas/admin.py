from pydantic import BaseModel, HttpUrl


class VideoSubmission(BaseModel):
    url: HttpUrl
    video_type: str
