import os
import re

from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve
from rerank import rerank
from context import build_context


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BASE_DIR / "prompts" / "system.txt"

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

CANDIDATE_LIMIT = 20
FINAL_LIMIT = 5
MAX_COMPLETION_TOKENS = 1200


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from your .env file.")

if not PROMPT_PATH.exists():
    raise FileNotFoundError(f"System prompt not found: {PROMPT_PATH}")

client = Groq(api_key=api_key)

SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


# --------------------------------------------------
# SOURCE FORMATTING
# --------------------------------------------------

def get_referenced_sources(answer, sources):
    """Return only sources whose IDs appear in the answer."""

    referenced_ids = set(
        re.findall(r"\[(S\d+)\]", answer)
    )

    return {
        source_id: sources[source_id]
        for source_id in sources
        if source_id in referenced_ids
    }


# --------------------------------------------------
# RAG PIPELINE
# --------------------------------------------------

def ask(question):

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    # 1. Hybrid retrieval
    print("\n[1/4] Retrieving relevant passages...")

    candidates = retrieve(
        question,
        limit=CANDIDATE_LIMIT,
    )

    if not candidates:
        print("No relevant passages found.")

    # 2. Reranking
    print("[2/4] Reranking passages...")

    ranked_results = rerank(
        question,
        candidates,
        limit=FINAL_LIMIT,
    )

    # 3. Context preparation
    print("[3/4] Preparing context...")

    prepared = build_context(ranked_results)

    context = prepared["context"]
    sources = prepared["sources"]

    if not context:
        context = "No relevant information was retrieved."

    # 4. LLM generation
    print("[4/4] Generating answer with Groq...")

    user_message = f"""
USER QUESTION:
{question}

RETRIEVED CONTEXT:
<context>
{context}
</context>

Answer the user's question using the instructions in the system prompt.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        max_tokens=MAX_COMPLETION_TOKENS,
        temperature=0.2,
    )

    answer = response.choices[0].message.content or ""

    referenced_sources = get_referenced_sources(answer, sources)

    return {
        "answer": answer,
        "sources": referenced_sources,
        "retrieved_count": len(candidates),
        "reranked_count": len(ranked_results),
    }


# --------------------------------------------------
# CLI
# --------------------------------------------------

if __name__ == "__main__":

    print("\n========== YOUTUBE KNOWLEDGE ASSISTANT ==========")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            result = ask(question)

            print("\n========== ANSWER ==========\n")
            print(result["answer"])

            print("\n========== REFERENCED SOURCES ==========\n")

            if result["sources"]:

                for source_id, source in result["sources"].items():

                    print(f"[{source_id}] {source['title']}")
                    print(f"Timestamp: {source['timestamp']}")
                    print(f"URL: {source['url']}\n")

            else:
                print("No source IDs were cited in the answer.")

            print(
                f"Retrieved: {result['retrieved_count']} | "
                f"Reranked: {result['reranked_count']}"
            )

        except Exception as error:
            print(f"\nError: {error}")