
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

load_dotenv()

COLLECTION = "youtube_knowledge_v3"

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=120
)

print("Loading dense model...")
dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

print("Loading sparse model...")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def retrieve(query, limit=5, domain=None):

    # Optional domain filter
    query_filter = None
    if domain and domain.strip().lower() != "all":
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="domains",
                    match=models.MatchValue(value=domain.strip().lower())
                )
            ]
        )

    # Dense query embedding
    dense_vector = dense_model.encode(
        "Represent this sentence for searching relevant passages: " + query,
        normalize_embeddings=True
    ).tolist()

    # Sparse BM25 query embedding
    sparse_vector = next(
        iter(sparse_model.query_embed([query]))
    )

    prefetch_dense = models.Prefetch(
        query=dense_vector,
        using="dense",
        limit=20
    )
    prefetch_sparse = models.Prefetch(
        query=models.SparseVector(
            indices=sparse_vector.indices.tolist(),
            values=sparse_vector.values.tolist()
        ),
        using="sparse",
        limit=20
    )

    if query_filter:
        prefetch_dense.filter = query_filter
        prefetch_sparse.filter = query_filter

    # Hybrid search with Reciprocal Rank Fusion
    response = client.query_points(
        collection_name=COLLECTION,
        prefetch=[prefetch_dense, prefetch_sparse],
        query=models.FusionQuery(
            fusion=models.Fusion.RRF
        ),
        limit=limit,
        with_payload=True
    )

    return response.points


def main():

    query = input("\nEnter your question: ").strip()

    if not query:
        print("Query cannot be empty.")
        return

    results = retrieve(query)

    print(f"\nRetrieved {len(results)} chunks")
    print("=" * 70)

    for index, point in enumerate(results, 1):

        payload = point.payload

        print(f"\nResult {index}")
        print(f"Score: {point.score:.4f}")
        print(f"Title: {payload.get('title')}")
        print(f"Domains: {payload.get('domains')}")
        print(f"Timestamp: {payload.get('timestamp', {}).get('start_formatted')}")
        print(f"URL: {payload.get('url')}")

        print("\nContent:")
        print(payload.get("text", "")[:1000])

        print("-" * 70)


if __name__ == "__main__":
    main()
