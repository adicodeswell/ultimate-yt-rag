
import json
import os
import uuid
import time
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION = "youtube_knowledge_v3"
INPUT = Path("data/knowledge_v2/knowledge_base.jsonl")

BATCH_SIZE = 32

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=120
)

print("Loading dense embedding model...")
dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

print("Loading sparse BM25 model...")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def make_point_id(chunk_id):
    return str(
        uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)
    )


def upload_batch(chunks):
    texts = [chunk["text"] for chunk in chunks]

    dense_vectors = dense_model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    sparse_vectors = list(
        sparse_model.embed(texts)
    )

    points = []

    for chunk, dense, sparse in zip(
        chunks,
        dense_vectors,
        sparse_vectors
    ):
        metadata = chunk["metadata"]

        point = models.PointStruct(
            id=make_point_id(chunk["id"]),
            vector={
                "dense": dense.tolist(),
                "sparse": models.SparseVector(
                    indices=sparse.indices.tolist(),
                    values=sparse.values.tolist()
                )
            },
            payload={
                "chunk_id": chunk["id"],
                "text": chunk["text"],
                **metadata
            }
        )

        points.append(point)

    for attempt in range(1, 4):
        try:
            client.upsert(
                collection_name=COLLECTION,
                points=points,
                wait=True
            )
            return

        except Exception as error:
            print(
                f"Upload failed "
                f"(attempt {attempt}/3): {error}"
            )

            if attempt == 3:
                raise

            time.sleep(5)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    total = 0
    batch = []

    print(f"\nReading: {INPUT}")

    with open(INPUT, encoding="utf-8") as file:
        for line in file:
            batch.append(json.loads(line))

            if len(batch) >= BATCH_SIZE:
                upload_batch(batch)
                total += len(batch)
                print(f"Uploaded: {total}")
                batch.clear()

        if batch:
            upload_batch(batch)
            total += len(batch)
            print(f"Uploaded: {total}")

    print("\nEmbedding complete.")
    print(f"Total uploaded: {total}")

    info = client.get_collection(COLLECTION)
    print(f"Qdrant points: {info.points_count}")


if __name__ == "__main__":
    main()
