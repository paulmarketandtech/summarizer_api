import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base(
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(
        String(1000), unique=True, index=True, nullable=False
    )
    yt_id: Mapped[str | None] = mapped_column(String(100), unique=True)

    title: Mapped[str | None] = mapped_column(String(500))
    yt_creator: Mapped[str | None] = mapped_column(String(500))
    published_date: Mapped[date | None] = mapped_column(Date, index=True)

    content_type: Mapped[str | None] = mapped_column(
        String(100), index=True
    )  # stock_analysis, drama queen, macro, etc.
    transcript_file_name: Mapped[str | None] = mapped_column(String(500))
    summary_file_name: Mapped[str | None] = mapped_column(String(500))
    summary_preview: Mapped[str | None] = mapped_column(String(500))

    transcript_char_length: Mapped[int | None] = mapped_column()
    transcript_word_count: Mapped[int | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    chunks: Mapped[list["TranscriptChunk"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="TranscriptChunk.chunk_index",
    )
    llm_chunks: Mapped[list["LLMChunkMetaData"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )
    summary: Mapped["Summary"] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        uselist=False,  # ← This makes it one-to-one
        foreign_keys="Summary.video_id",
    )
    stockSummaries: Mapped[list["SingleStockSummary"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
        }


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    __table_args__ = (
        UniqueConstraint("video_id", "chunk_index", name="uq_video_chunk_index"),
        Index("idx_video_chunk", "video_id", "chunk_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    char_count: Mapped[int | None] = mapped_column()
    word_count: Mapped[int | None] = mapped_column()
    sentence_count: Mapped[int | None] = mapped_column()

    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Relationship
    video: Mapped["Video"] = relationship(back_populates="chunks")


class LLMChunkMetaData(Base):
    __tablename__ = "llm_chunk_metadata"
    __table_args__ = (
        UniqueConstraint("video_id", "chunk_index", name="uq_video_llmchunk_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100))
    created_at_llm: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    eval_count: Mapped[int | None] = mapped_column()
    eval_duration: Mapped[float | None] = mapped_column()
    tokens_per_second: Mapped[float | None] = mapped_column()
    prompt_eval_count: Mapped[int | None] = mapped_column()
    prompt_eval_duration: Mapped[float | None] = mapped_column()
    load_duration: Mapped[float | None] = mapped_column()
    total_duration: Mapped[float | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Relationship
    video: Mapped["Video"] = relationship(back_populates="llm_chunks")


class Summary(Base):
    __tablename__ = "transcript_summaries"
    __table_args__ = (
        UniqueConstraint("video_id", "final_report", name="uq_video_summary"),
        Index("idx_video_summary", "video_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # ← Unique for one-to-one
    )

    final_report: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int | None] = mapped_column()
    word_count: Mapped[int | None] = mapped_column()
    processing_time_seconds: Mapped[float | None] = mapped_column()

    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    video: Mapped["Video"] = relationship(back_populates="summary")


class SingleStockSummary(Base):
    __tablename__ = "single_stock_summary"
    __table_args__ = (
        UniqueConstraint("video_id", "stock_name", name="uq_video_stockSummary"),
        Index("idx_video_stockSummary", "video_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_name: Mapped[str | None] = mapped_column(String(100))
    stock_full_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int | None] = mapped_column()
    word_count: Mapped[int | None] = mapped_column()

    model_used: Mapped[str | None] = mapped_column(String(100))
    created_at_llm: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    eval_count: Mapped[int | None] = mapped_column()
    eval_duration: Mapped[float | None] = mapped_column()
    tokens_per_second: Mapped[float | None] = mapped_column()
    prompt_eval_count: Mapped[int | None] = mapped_column()
    prompt_eval_duration: Mapped[float | None] = mapped_column()
    load_duration: Mapped[float | None] = mapped_column()
    total_duration: Mapped[float | None] = mapped_column()
    system_prompt_used: Mapped[str | None] = mapped_column(String(100))
    user_prompt_used: Mapped[str | None] = mapped_column(String(100))

    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    video: Mapped["Video"] = relationship(back_populates="stockSummaries")


class VideoTag(Base):
    __tablename__ = "video_tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_type: Mapped[str | None] = mapped_column(String(50))
    tag_value: Mapped[str | None] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
