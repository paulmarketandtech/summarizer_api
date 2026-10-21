from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session, selectinload

from src.storage.models import Summary, Video


@dataclass
class VideoRecord:
    """Flexible video record - add/remove fields as needed"""

    id: str
    title: str
    url: str
    yt_id: str
    published_date: datetime | None
    content_type: str
    summary: str | None
    summary_preview: str | None
    transcript_word_count: int | None
    creator: str | None
    created_at: datetime


class VideoQueryService:
    def __init__(self, session: Session):
        self.session = session

    def get_videos_basic(self, limit: int = 50) -> tuple[list[VideoRecord], int]:
        stmt = (
            select(Video)
            .options(selectinload(Video.summary))
            .order_by(desc(Video.published_date))
            .limit(limit)
        )

        videos = self.session.execute(stmt).scalars().all()

        return (
            [
                VideoRecord(
                    id=str(video.id),
                    title=video.title,
                    url=video.url,
                    yt_id=video.yt_id,
                    published_date=video.published_date,
                    content_type=video.content_type,
                    summary=video.summary.final_report if video.summary else None,
                    summary_preview=video.summary_preview,
                    transcript_word_count=video.transcript_word_count,
                    creator=video.yt_creator,
                    created_at=video.created_at,
                )
                for video in videos
            ],
            len(videos),
        )

    # TODO: not in use. delete?
    def get_videos_by_content_type(
        self, content_type: str, limit: int = 50
    ) -> list[VideoRecord]:
        """Get videos filtered by content type"""
        stmt = (
            select(Video)
            .options(selectinload(Video.summary))
            .where(Video.content_type == content_type)
            .order_by(desc(Video.published_date))
            .limit(limit)
        )

        videos = self.session.execute(stmt).scalars().all()

        return [
            VideoRecord(
                id=str(video.id),
                title=video.title,
                url=video.url,
                yt_id=video.yt_id,
                published_date=video.published_date,
                content_type=video.content_type,
                summary=video.summary.final_report if video.summary else None,
                summary_preview=video.summary_preview,
                transcript_word_count=video.transcript_word_count,
                creator=video.yt_creator,
                created_at=video.created_at,
            )
            for video in videos
        ]

    def get_videos_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 50
    ) -> list[VideoRecord]:
        stmt = (
            select(Video)
            .options(selectinload(Video.summary))
            .where(
                and_(
                    Video.published_date >= start_date, Video.published_date <= end_date
                )
            )
            .order_by(desc(Video.published_date))
            .limit(limit)
        )

        videos = self.session.execute(stmt).scalars().all()

        return [self._to_record(video) for video in videos]

    def get_video_by_yt_id(self, yt_id: str):
        return (
            self.session.query(Video.title, Video.summary)
            .filter(Video.yt_id == yt_id)
            .all()
        )

    def search_by_title(self, query: str, limit: int = 50) -> list[VideoRecord]:
        stmt = (
            select(Video)
            .options(selectinload(Video.summary))
            .where(Video.title.ilike(f"%{query}%"))
            .order_by(desc(Video.published_date))
            .limit(limit)
        )

        videos = self.session.execute(stmt).scalars().all()

        return [self._to_record(video) for video in videos]

    def search_by_creator(self, creator: str, limit: int = 50) -> list[VideoRecord]:
        stmt = (
            select(Video)
            .options(selectinload(Video.summary))
            .where(Video.yt_creator.ilike(f"%{creator}%"))
            .order_by(desc(Video.published_date))
            .limit(limit)
        )

        videos = self.session.execute(stmt).scalars().all()

        return [self._to_record(video) for video in videos]

    def get_stats(self) -> dict:
        total_videos = self.session.query(Video).count()
        total_summaries = self.session.query(Summary).count()

        content_types = self.session.query(Video.content_type).distinct().all()

        return {
            "total_videos": total_videos,
            "total_summaries": total_summaries,
            "content_types": [ct[0] for ct in content_types if ct[0]],
        }

    # Helper method
    def _to_record(self, video: Video) -> VideoRecord:
        """Convert Video ORM object to VideoRecord dataclass"""
        return VideoRecord(
            id=str(video.id),
            title=video.title,
            url=video.url,
            yt_id=video.yt_id,
            published_date=video.published_date,
            content_type=video.content_type,
            summary=video.summary.final_report if video.summary else None,
            summary_preview=video.summary_preview,
            transcript_word_count=video.transcript_word_count,
            creator=video.yt_creator,
            created_at=video.created_at,
        )
