from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.services.embeddings import EmbeddingService
from app.storage.database import get_session
from app.storage.models import SingleStockSummary, TranscriptChunk, Video

MIN_SIMILARITY = 0.60
PER_VIDEO_CAP = 2


@dataclass
class SearchHit:
    video_id: str
    text: str
    source: str
    similarity: float


class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.embedder = EmbeddingService()

    def _search_table(
        self, model, text_col, query_vector, limit, label_fn, extra_filters=None
    ):
        q = self.db.query(
            model.video_id,
            text_col.label("text"),
            model.embedding.cosine_distance(query_vector).label("distance"),
            model,
        ).filter(model.embedding.isnot(None))
        for f in extra_filters or []:
            q = q.filter(f)

        rows = q.order_by("distance").limit(limit).all()
        return [
            SearchHit(str(r.video_id), r.text, label_fn(r), round(1 - r.distance, 4))
            for r in rows
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = MIN_SIMILARITY,
        chunk_filters=None,
        stock_filters=None,
        # company_names=None,
    ) -> list[SearchHit]:
        qv = self.embedder.embed_text_sync(query)

        hits = self._search_table(
            TranscriptChunk,
            TranscriptChunk.chunk_text,
            qv,
            limit=top_k * 4,
            label_fn=lambda r: "chunk",
            extra_filters=chunk_filters,
        ) + self._search_table(
            SingleStockSummary,
            SingleStockSummary.stock_full_text,
            qv,
            limit=top_k * 4,
            label_fn=lambda r: f"stock: {r[3].stock_name}",
            extra_filters=stock_filters,
        )

        hits = [h for h in hits if h.similarity >= min_similarity]
        hits.sort(key=lambda h: h.similarity, reverse=True)

        # cap per video so one talkative video doesn't dominate
        seen: dict[str, int] = {}
        out = []
        for h in hits:
            n = seen.get(h.video_id, 0)
            if n >= PER_VIDEO_CAP:
                continue
            seen[h.video_id] = n + 1
            out.append(h)
            if len(out) == top_k:
                break
        return out

    def search_filtered(
        self,
        query: str,
        ticker: str | None = None,
        after: date | None = None,
        before: date | None = None,
        top_k: int = 5,
    ):
        chunk_f, stock_f = [], []

        if ticker:
            stock_f.append(SingleStockSummary.stock_name.ilike(ticker))

        if after or before:
            vids = self.db.query(Video.id)
            if after:
                vids = vids.filter(Video.published_at >= after)
            if before:
                vids = vids.filter(Video.published_at <= before)
            ids = [v.id for v in vids]
            chunk_f.append(TranscriptChunk.video_id.in_(ids))
            stock_f.append(SingleStockSummary.video_id.in_(ids))

        return self.search(query, top_k, chunk_filters=chunk_f, stock_filters=stock_f)


with get_session() as session:
    rag = RagService(session)

"""
queries = [
    "nvidia earnings",  # should hit
    "what does he think about AMD",  # should hit
    "pizza recipe",  # should miss
    "how to fix a bicycle tyre",  # should miss
    "the weather in Poland",  # should miss
]

for q in queries:
    hits = rag.search(q, top_k=3)
    print(f"\n{q}")
    print("-" * 50)
    for h in hits:
        print("+" * 50)
        print(f"  {h.similarity:.3f} \n {h.source} \n {h.text[:60]} ||\n")
        # print(f"  {h['similarity']:.3f} \n {h['source']} \n {h['text'][:60]} ||\n")
"""
