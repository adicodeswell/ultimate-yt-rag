
from sentence_transformers import CrossEncoder

from retrieve import retrieve


MODEL_NAME = "BAAI/bge-reranker-base"

CANDIDATE_LIMIT = 20
FINAL_LIMIT = 5

print("Loading reranker...")
reranker = CrossEncoder(MODEL_NAME)


def rerank(query, candidates, limit=FINAL_LIMIT):

    if not candidates:
        return []

    pairs = [
        [query, point.payload.get("text", "")]
        for point in candidates
    ]

    scores = reranker.predict(
        pairs,
        batch_size=8,
        show_progress_bar=False
    )

    ranked = sorted(
        zip(candidates, scores),
        key=lambda item: float(item[1]),
        reverse=True
    )

    results = []

    for point, score in ranked[:limit]:
        results.append({
            "score": float(score),
            "payload": point.payload
        })

    return results


def main():

    query = input("\nEnter your question: ").strip()

    if not query:
        print("Query cannot be empty.")
        return

    print("\nRetrieving candidates...")

    candidates = retrieve(
        query,
        limit=CANDIDATE_LIMIT
    )

    print(f"Retrieved {len(candidates)} candidates.")
    print("\nReranking...")

    results = rerank(query, candidates)

    for index, result in enumerate(results, 1):

        payload = result["payload"]

        print(f"\n{'=' * 70}")
        print(f"Rank: {index}")
        print(f"Reranker score: {result['score']:.4f}")
        print(f"Title: {payload.get('title')}")
        print(f"Domains: {payload.get('domains')}")
        print(f"Timestamp: {payload.get('timestamp', {}).get('start_formatted')}")
        print(f"URL: {payload.get('url')}")
        print(f"\n{payload.get('text', '')[:1000]}")

    print("\nReranking complete.")


if __name__ == "__main__":
    main()
