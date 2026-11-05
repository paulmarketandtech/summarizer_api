import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db_write
from app.processors.db_population import update_full_processing_time
from app.schemas.admin import VideoSubmission
from app.schemas.summary import TitlesOut
from app.storage.database import get_session
from app.storage.models import Video
from app.utils.check_video_processed import check_id_in_db, get_processed_summary
from pipeline import PipelineConfig, get_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class VideoResponse(BaseModel):
    status: str  # "cached" or "processed"
    title: str
    summary: str
    video_type: str
    processing_time: float | None = None


@router.post("/videos", response_model=VideoResponse)
async def submit_video(
    submission: VideoSubmission,
    db: Annotated[Session, Depends(get_db_write)],
):
    url = str(submission.url)

    try:
        video_processed, yt_id = check_id_in_db(url)
    except Exception as e:
        logger.exception("DB lookup failed")
        raise HTTPException(status_code=500, detail=f"DB lookup failed: {e}")

    if video_processed:
        try:
            title, summary = get_processed_summary(yt_id)
        except Exception as e:
            logger.exception("Failed to fetch summary")
            raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {e}")

        return VideoResponse(
            status="cached",
            title=title,
            summary=summary,
            video_type=submission.video_type,
        )

    try:
        start_time = time.perf_counter()

        cfg = PipelineConfig(
            source=url,
            is_url=True,
            run_tag="strict_v3",
            # TODO: pass submission.video_type here when you wire up prompt selection
        )
        ctx = get_pipeline().run(cfg)

        processing_time = time.perf_counter() - start_time
        update_full_processing_time(processing_time, yt_id)

        # Adjust these keys to match your actual pipeline context structure
        title = ctx.get("fetch_transcript", {}).get("title", "Unknown Titleaa")
        summary = ctx["process"]["final_report"]

    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    return VideoResponse(
        status="processed",
        title=title,
        summary=summary,
        video_type=submission.video_type,
        processing_time=round(processing_time, 2),
    )


"""
@router.post("/videos")
async def submit_video(
    submission: VideoSubmission, db: Annotated[Session, Depends(get_db_write)]
):
    if os.getenv("APP_MODE") == "prod":
        video_processed, yt_id = check_id_in_db(url)
        if video_processed:
            print("Video was already processed. Here you are!")
            processed_title, processed_summary = get_processed_summary(yt_id)
            print(f"{processed_title}\n---\n{processed_summary}")
        else:
            print("processing a new video")
            start_time = time.perf_counter()
            cfg = PipelineConfig(source=url, is_url=True, run_tag="strict_v3")
            ctx = get_pipeline().run(cfg)
            print(ctx["process"]["final_report"])
            processing_time = time.perf_counter() - start_time
            update_full_processing_time(processing_time, yt_id)
            print(processing_time)

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
"""


# TODO: to be deleted? this one and the one below
@router.get("/titles", response_model=TitlesOut)
def get_titles():
    with get_session() as session:
        titles = session.scalars(select(Video.title)).all()  # list[str]
        return TitlesOut(titles=titles)


@router.post("/feed")
def feed_video(
    db: Annotated[Session, Depends(get_db_write)],
    url: str,
):
    return {"status": "created"}
