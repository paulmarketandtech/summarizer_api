import os

import chromadb  # pyright: ignore
from dotenv import load_dotenv

load_dotenv()

chromadb_path = os.getenv("CHROMADB_STORAGE_PATH")


# TODO: persist_dir not in use anymore, goes directly to LXC
class VectorDBManager:
    def __init__(self, persist_dir=chromadb_path):
        """
        Initialize ChromaDB client

        ChromaDB stores:
        1. Vectors (in HNSW index)
        2. Metadata (in SQLite)
        3. Documents (in persistent storage)
        """
        # self.persist_dir = Path(persist_dir)  # pyright: ignore
        # self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize persistent client
        # self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.client = chromadb.HttpClient(host="192.168.0.164", port=8000)

        # Get/create collections
        self.original_chunks_collection = self.client.get_or_create_collection(
            name="transcript_chunks",
            metadata={
                "hnsw:space": "cosine",  # similarity metric
                "description": "Vectorized transcript chunks",
            },
        )

        self.stock_summary_collection = self.client.get_or_create_collection(
            name="stock_summaries",
            metadata={
                "hnsw:space": "cosine",
                "description": "Vectorized stocks summaries",
            },
        )

        self.video_summary_collection = self.client.get_or_create_collection(
            name="video_summaries",
            metadata={
                "hnsw:space": "cosine",
                "description": "Vectorized video summaries",
            },
        )

    def add_original_chunk(self, chunk_ids: list, texts: list, metadatas: list) -> str:
        """
        Add a transcript chunk to vector DB

        Args:
            chunk_id: unique identifier (video_id_chunk_index)
            text: the chunk text
            metadata: dict with video_id, chunk_index, source_type, etc.

        Returns:
            The chunk_id (for storing in SQL DB)
        """
        self.original_chunks_collection.add(
            ids=chunk_ids, documents=texts, metadatas=metadatas
        )
        print(chunk_ids[0])
        return chunk_ids[0]

    def add_stock_summary(self, summary_ids: list, texts: list, metadatas: list) -> str:
        """
        Add a stock summary to vector DB
        Returns:
            The summary_id
        """
        self.stock_summary_collection.add(
            ids=summary_ids, documents=texts, metadatas=metadatas
        )
        print(summary_ids[0])
        return summary_ids[0]

    def add_video_summary(self, summary_id: str, text: str, metadata: list) -> str:
        self.video_summary_collection.add(
            ids=[summary_id], documents=[text], metadatas=metadata
        )
        print(summary_id)
        return summary_id

    def search_chunks(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> dict:
        """
        Semantic search in transcript chunks

        Args:
            query_text: "What did they say about Nvidia?"
            n_results: top 5 most similar chunks
            filter_metadata: {"content_type": "stock_analysis"}

        Returns:
            {
                'ids': [...],
                'documents': [...],
                'metadatas': [...],
                'distances': [0.1, 0.15, ...]  # lower = more similar
            }
        """
        results = self.original_chunks_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            # where=filter_metadata if filter_metadata else None,
        )

        print("=" * 40)
        __import__("pprint").pprint(results)
        print("=" * 40)
        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0],
        }

    def search_stock_summaries(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> dict:
        results = self.stock_summary_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata if filter_metadata else None,
        )

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0],
        }

    def search_video_summaries(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: dict | None = None,
    ) -> dict:
        results = self.video_summary_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata if filter_metadata else None,
        )

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0],
        }

    def get_chunk(self, chunk_id: str) -> dict | None:
        results = self.original_chunks_collection.get(ids=[chunk_id])
        if results["documents"]:
            return {
                "id": results["ids"][0],
                "text": results["documents"][0],
                "metadata": results["metadatas"][0],
            }
        return None

    def get_stock_summary(self, summary_id: str) -> dict | None:
        results = self.video_summary_collection.get(ids=[summary_id])
        if results["documents"]:
            return {
                "id": results["ids"][0],
                "text": results["documents"][0],
                "metadata": results["metadatas"][0],
            }
        return None

    def get_video_summary(self, summary_id: str) -> dict | None:
        results = self.video_summary_collection.get(ids=[summary_id])
        if results["documents"]:
            return {
                "id": results["ids"][0],
                "text": results["documents"][0],
                "metadata": results["metadatas"][0],
            }
        return None

    def delete_video(self, video_id: str):
        """Delete all vectors associated with a video"""
        # Delete chunks
        chunk_ids = self.original_chunks_collection.get(
            where={"video_id": {"$eq": video_id}}
        )["ids"]
        if chunk_ids:
            self.original_chunks_collection.delete(ids=chunk_ids)

        # Delete summary
        self.stock_summary_collection.delete(ids=[video_id])
        self.video_summary_collection.delete(ids=[video_id])

    def get_stats(self) -> dict:
        return {
            "chunk_count": self.original_chunks_collection.count(),
            "stock_count": self.stock_summary_collection.count(),
            "video_count": self.video_summary_collection.count(),
        }
