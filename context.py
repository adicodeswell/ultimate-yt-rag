import re


DEFAULT_MAX_CHARS = 12_000
DEFAULT_MAX_RESULTS = 5


def get_timestamp(payload):
    """Extract a readable timestamp from different payload formats."""

    timestamp = payload.get("timestamp")

    if isinstance(timestamp, dict):
        start = timestamp.get("start_formatted") or timestamp.get("start")
        end = timestamp.get("end_formatted") or timestamp.get("end")

        if start and end:
            return f"{start} - {end}"
        return str(start or end or "Unknown")

    if isinstance(timestamp, str):
        return timestamp

    start = payload.get("start_formatted")
    end = payload.get("end_formatted")

    if start and end:
        return f"{start} - {end}"

    return str(start or end or "Unknown")


def build_context(
    ranked_results,
    max_chars=DEFAULT_MAX_CHARS,
    max_results=DEFAULT_MAX_RESULTS,
):
    """
    Convert reranked results into LLM-ready context.

    Returns:
        {
            "context": formatted context string,
            "sources": source reference dictionary
        }
    """

    context_parts = []
    sources = {}

    seen_ids = set()
    seen_text = set()
    current_chars = 0

    for result in ranked_results:

        payload = result["payload"]

        text = payload.get("text", "").strip()

        if not text:
            continue

        # Remove exact duplicate chunks.
        chunk_id = payload.get("chunk_id") or payload.get("id")

        normalized_text = re.sub(r"\s+", " ", text).lower()

        if chunk_id and chunk_id in seen_ids:
            continue

        if normalized_text in seen_text:
            continue

        seen_ids.add(chunk_id)
        seen_text.add(normalized_text)

        source_id = f"S{len(sources) + 1}"

        title = payload.get("title", "Unknown video")
        url = payload.get("url", "Unavailable")
        timestamp = get_timestamp(payload)

        # Keep metadata outside the evidence text.
        source_header = (
            f"[{source_id}]\n"
            f"Title: {title}\n"
            f"Timestamp: {timestamp}\n"
            f"URL: {url}\n"
            f"Content:\n"
        )

        remaining = max_chars - current_chars

        if remaining <= len(source_header):
            break

        available_text = remaining - len(source_header)

        if len(text) > available_text:
            text = text[:available_text].rsplit(" ", 1)[0]

        if not text:
            break

        block = source_header + text

        context_parts.append(block)

        sources[source_id] = {
            "title": title,
            "timestamp": timestamp,
            "url": url,
        }

        current_chars += len(block)

        if current_chars >= max_chars:
            break

        if len(sources) >= max_results:
            break

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources,
    }


if __name__ == "__main__":
    from retrieve import retrieve
    from rerank import rerank

    query = input("Enter your question: ").strip()

    if not query:
        raise SystemExit("Question cannot be empty.")

    print("\nRetrieving candidates...")
    candidates = retrieve(query, limit=20)

    print("Reranking candidates...")
    ranked_results = rerank(query, candidates, limit=5)

    print("Preparing context...")
    result = build_context(ranked_results)

    print("\n========== CONTEXT ==========\n")
    print(result["context"])

    print("\n========== SOURCES ==========\n")

    for source_id, source in result["sources"].items():
        print(f"[{source_id}] {source['title']}")
        print(f"Timestamp: {source['timestamp']}")
        print(f"URL: {source['url']}\n")