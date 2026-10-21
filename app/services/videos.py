from sqlalchemy import distinct, select
from sqlalchemy.orm import Session, joinedload

from app.schemas.video import FilterOptions, VideoDetailPublic, VideoPublic
from app.storage.models import Video


class VideoService:
    def __init__(self, db: Session):
        self.db = db

    def list_latest(self, limit: int = 10) -> list[VideoPublic]:
        videos = (
            self.db.query(Video)
            .order_by(Video.published_date.desc().nullslast())
            .limit(limit)
            .all()
        )
        return [VideoPublic.model_validate(v) for v in videos]

    def list_filtered(
        self,
        creator: str | None = None,
        content_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
    ) -> list[VideoPublic]:
        query = self.db.query(Video)
        if creator:
            query = query.filter(Video.yt_creator == creator)
        if content_type:
            query = query.filter(Video.content_type == content_type)
        if date_from:
            query = query.filter(Video.published_date >= date_from)
        if date_to:
            query = query.filter(Video.published_date <= date_to)
        videos = (
            query.order_by(Video.published_date.desc().nullslast()).limit(limit).all()
        )
        return [VideoPublic.model_validate(v) for v in videos]

    def get_detail(self, video_id) -> VideoDetailPublic | None:
        video = (
            self.db.query(Video)
            .options(joinedload(Video.summary))
            .filter(Video.id == video_id)
            .first()
        )
        if not video:
            return None
        data = VideoPublic.model_validate(video).model_dump()
        data["summary"] = video.summary.final_report if video.summary else None
        return VideoDetailPublic(**data)

    def get_filter_options(self) -> FilterOptions:
        creators = self.db.scalars(
            select(distinct(Video.yt_creator))
            .where(Video.yt_creator.isnot(None))
            .order_by(Video.yt_creator)
        ).all()
        content_types = self.db.scalars(
            select(distinct(Video.content_type))
            .where(Video.content_type.isnot(None))
            .order_by(Video.content_type)
        ).all()
        return FilterOptions(creators=creators, content_types=content_types)
