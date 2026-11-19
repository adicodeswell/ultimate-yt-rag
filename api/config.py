import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION", "youtube_knowledge_v3")

    DENSE_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    SPARSE_MODEL_NAME: str = "Qdrant/bm25"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-base"

    CANDIDATE_LIMIT: int = 60
    DEFAULT_LIMIT: int = 5
    MAX_LIMIT: int = 10

    # CORS origins for frontend (Vite default is 5173)
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
