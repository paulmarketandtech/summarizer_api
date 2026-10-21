from sqlalchemy.orm import Session

from app.services.embeddings import EmbeddingService
from app.storage.models import SingleStockSummary, Summary, TranscriptChunk


class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.embedder = EmbeddingService()

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search across chunks, summaries, and stock summaries."""

        # 1. Embed the user's question (sync call to your AI Hub)
        query_vector = self.embedder.embed_text_sync(query)

        results = []

        # 2. Search chunks
        chunks = (
            self.db.query(
                TranscriptChunk.video_id,
                TranscriptChunk.chunk_text.label("text"),
                TranscriptChunk.embedding.cosine_distance(query_vector).label(
                    "distance"
                ),
            )
            .filter(TranscriptChunk.embedding.isnot(None))
            .order_by("distance")
            .limit(top_k)
            .all()
        )
        for row in chunks:
            results.append(
                {
                    "video_id": str(row.video_id),
                    "text": row.text,
                    "source": "chunk",
                    "similarity": round(1 - row.distance, 4),
                }
            )

        # 3. Search full summaries
        summaries = (
            self.db.query(
                Summary.video_id,
                Summary.final_report.label("text"),
                Summary.embedding.cosine_distance(query_vector).label("distance"),
            )
            .filter(Summary.embedding.isnot(None))
            .order_by("distance")
            .limit(top_k)
            .all()
        )
        for row in summaries:
            results.append(
                {
                    "video_id": str(row.video_id),
                    "text": row.text,
                    "source": "summary",
                    "similarity": round(1 - row.distance, 4),
                }
            )

        # 4. Search stock summaries
        stocks = (
            self.db.query(
                SingleStockSummary.video_id,
                SingleStockSummary.stock_name,
                SingleStockSummary.stock_full_text.label("text"),
                SingleStockSummary.embedding.cosine_distance(query_vector).label(
                    "distance"
                ),
            )
            .filter(SingleStockSummary.embedding.isnot(None))
            .order_by("distance")
            .limit(top_k)
            .all()
        )
        for row in stocks:
            results.append(
                {
                    "video_id": str(row.video_id),
                    "text": row.text,
                    "source": f"stock: {row.stock_name}",
                    "similarity": round(1 - row.distance, 4),
                }
            )

        # 5. Combine all results, sort by similarity, take top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
