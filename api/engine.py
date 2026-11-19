import logging
from typing import Optional, List
from sentence_transformers import SentenceTransformer, CrossEncoder
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from api.config import settings
from api.schema import SearchResultItem

logger = logging.getLogger(__name__)


def format_time(seconds: float) -> str:
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    rem = secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{rem:02d}"
    return f"{minutes:02d}:{rem:02d}"


class SearchEngine:
    def __init__(self):
        logger.info("Initializing Qdrant client...")
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=120,
            check_compatibility=False
        )
        self.collection = settings.COLLECTION_NAME

        logger.info(f"Loading dense model: {settings.DENSE_MODEL_NAME}...")
        self.dense_model = SentenceTransformer(settings.DENSE_MODEL_NAME)

        logger.info(f"Loading sparse model: {settings.SPARSE_MODEL_NAME}...")
        self.sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_MODEL_NAME)

        logger.info(f"Loading reranker model: {settings.RERANKER_MODEL_NAME}...")
        self.reranker = CrossEncoder(settings.RERANKER_MODEL_NAME)

        logger.info("Search engine initialization complete.")

    def search(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = settings.DEFAULT_LIMIT
    ) -> List[SearchResultItem]:
        query = query.strip()
        if not query:
            return []

        # 1. Build optional domain filter for Qdrant
        query_filter = None
        if domain and domain.strip().lower() != "all":
            normalized_domain = domain.strip().lower()
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="domains",
                        match=models.MatchValue(value=normalized_domain)
                    )
                ]
            )

        # 2. Dense query embedding
        dense_vector = self.dense_model.encode(
            "Represent this sentence for searching relevant passages: " + query,
            normalize_embeddings=True
        ).tolist()

        # 3. Sparse BM25 query embedding
        sparse_vector = next(
            iter(self.sparse_model.query_embed([query]))
        )

        # 4. Hybrid search with Reciprocal Rank Fusion
        candidate_limit = max(settings.CANDIDATE_LIMIT, limit)

        prefetch_dense = models.Prefetch(
            query=dense_vector,
            using="dense",
            limit=candidate_limit
        )
        prefetch_sparse = models.Prefetch(
            query=models.SparseVector(
                indices=sparse_vector.indices.tolist(),
                values=sparse_vector.values.tolist()
            ),
            using="sparse",
            limit=candidate_limit
        )

        if query_filter:
            prefetch_dense.filter = query_filter
            prefetch_sparse.filter = query_filter

        response = self.client.query_points(
            collection_name=self.collection,
            prefetch=[prefetch_dense, prefetch_sparse],
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            limit=candidate_limit,
            with_payload=True
        )

        candidates = response.points
        if not candidates:
            return []

        # 5. Cross-encoder Reranking
        pairs = [
            [query, point.payload.get("text", "")]
            for point in candidates
        ]

        scores = self.reranker.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False
        )

        ranked = sorted(
            zip(candidates, scores),
            key=lambda item: float(item[1]),
            reverse=True
        )

        # 6. Map to agreed SearchResultItem schema
        results: List[SearchResultItem] = []
        for rank, (point, _score) in enumerate(ranked[:limit], start=1):
            payload = point.payload or {}
            timestamp = payload.get("timestamp") or {}

            chunk_id = str(payload.get("chunk_id") or point.id)
            video_id = str(payload.get("video_id") or "")
            title = str(payload.get("title") or "Untitled")

            start_sec = float(timestamp.get("start", 0.0))
            end_sec = float(timestamp.get("end", 0.0))

            start_formatted = timestamp.get("start_formatted") or format_time(start_sec)
            end_formatted = timestamp.get("end_formatted") or format_time(end_sec)

            # Build canonical watch URL
            video_url = payload.get("url")
            if not video_url and video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}&t={int(start_sec)}s"

            domains = payload.get("domains") or []
            if isinstance(domains, str):
                domains = [domains]

            text = str(payload.get("text") or "")

            results.append(
                SearchResultItem(
                    id=chunk_id,
                    rank=rank,
                    title=title,
                    video_id=video_id,
                    video_url=str(video_url),
                    start=start_sec,
                    end=end_sec,
                    start_formatted=start_formatted,
                    end_formatted=end_formatted,
                    domains=list(domains),
                    text=text
                )
            )

        return results
