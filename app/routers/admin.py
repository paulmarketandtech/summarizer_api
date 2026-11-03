from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db_write, require_api_key  # ← read-write + auth
from app.schemas.summary import TitlesOut
from app.storage.database import get_session
from app.storage.models import Video

router = APIRouter(prefix="/api/admin", tags=["admin"])

"""
example functions for reference
"""


@router.get("/titles", response_model=TitlesOut)
def get_titles():
    with get_session() as session:
        titles = session.scalars(select(Video.title)).all()  # list[str]
        return TitlesOut(titles=titles)


@router.post("/feed", dependencies=[Depends(require_api_key)])
def feed_video(
    db: Annotated[Session, Depends(get_db_write)],
    url: str,
):
    # This session CAN write. Protected by API key.
    new_video = Video(url=url)
    db.add(new_video)
    db.commit()
    return {"status": "created"}


router = APIRouter(
    prefix="/api/admin",
    dependencies=[Depends(require_api_key)],
)


@router.post("/videos")
async def submit_video(submission: VideoSubmission, db=Depends(get_db_write)):
    # This is where your processing pipeline will go:
    # 1. Extract video ID from URL
    # 2. Fetch transcript
    # 3. Pick prompt based on video_type
    # 4. Send to Ollama for summary
    # 5. Generate embeddings
    # 6. Store everything in DB

    # For now, just echo back to prove the wiring works:
    return {
        "status": "received",
        "url": str(submission.url),
        "video_type": submission.video_type,
    }
