
import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION = "youtube_knowledge_v3"

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=120
)


def create_collection():
    if client.collection_exists(COLLECTION):
        print(f"Collection already exists: {COLLECTION}")
        return

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={
            "dense": models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(
                index=models.SparseIndexParams(
                    on_disk=False
                )
            )
        }
    )

    print(f"Created collection: {COLLECTION}")


def create_payload_indexes():
    indexes = {
        "domains": models.PayloadSchemaType.KEYWORD,
        "metadata.playlists.playlist_id": models.PayloadSchemaType.KEYWORD,
        "metadata.video_id": models.PayloadSchemaType.KEYWORD
    }

    for field, schema in indexes.items():
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name=field,
            field_schema=schema,
            wait=True
        )
        print(f"Created index: {field}")


if __name__ == "__main__":
    create_collection()
    create_payload_indexes()
    print("Collection setup complete.")
