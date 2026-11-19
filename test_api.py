from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "collection" in data


def test_empty_query():
    response = client.post("/search", json={"query": "   "})
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_QUERY"


def test_valid_search_with_domain():
    response = client.post(
        "/search",
        json={
            "query": "Explain TCP three-way handshake",
            "domain": "backend",
            "limit": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert len(data["results"]) <= 3

    if data["results"]:
        first = data["results"][0]
        required_fields = [
            "id", "rank", "title", "video_id", "video_url",
            "start", "end", "start_formatted", "end_formatted",
            "domains", "text"
        ]
        for field in required_fields:
            assert field in first, f"Missing required field: {field}"
        assert first["rank"] == 1
        assert "backend" in [d.lower() for d in first["domains"]]


def test_limit_validation():
    response = client.post("/search", json={"query": "SQL indexing", "limit": 25})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    with TestClient(app) as test_client:
        print("Running backend tests...")
        test_health()
        print("✓ GET /health passed")
        test_empty_query()
        print("✓ POST /search empty query validation passed")
        test_limit_validation()
        print("✓ POST /search limit validation passed")
        test_valid_search_with_domain()
        print("✓ POST /search hybrid search + reranking passed")
        print("\nAll backend tests passed successfully!")
