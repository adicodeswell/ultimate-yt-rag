
import json
from collections import Counter
from pathlib import Path

INPUT = Path("data/chunks/knowledge_base.jsonl")
KNOWLEDGE_DIR = Path("data/knowledge")

OUTPUT_DIR = Path("data/knowledge_v2")
OUTPUT = OUTPUT_DIR / "knowledge_base.jsonl"


def load_domain_assignments():
    assignments = {}

    for file in KNOWLEDGE_DIR.glob("*.jsonl"):
        domain = file.stem

        with open(file, encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                chunk_id = chunk["id"]

                assignments.setdefault(chunk_id, set())
                assignments[chunk_id].add(domain)

    return assignments


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    assignments = load_domain_assignments()

    counts = Counter()
    total = 0
    multi_domain = 0

    with open(INPUT, encoding="utf-8") as source, \
         open(OUTPUT, "w", encoding="utf-8") as output:

        for line in source:
            chunk = json.loads(line)

            chunk_id = chunk["id"]

            domains = assignments.get(chunk_id, {"other"})

            # "other" should only remain if no meaningful
            # domain was assigned.
            meaningful = domains - {"other"}

            if meaningful:
                domains = meaningful
            else:
                domains = {"other"}

            domains = sorted(domains)

            metadata = {
                **chunk["metadata"],
                "domains": domains
            }

            new_chunk = {
                "id": chunk_id,
                "text": chunk["text"],
                "metadata": metadata
            }

            output.write(
                json.dumps(new_chunk, ensure_ascii=False) + "\n"
            )

            total += 1

            if len(domains) > 1:
                multi_domain += 1

            for domain in domains:
                counts[domain] += 1

    print("\n========== NEW KNOWLEDGE BASE ==========")
    print(f"Total chunks: {total}")
    print(f"Multi-domain chunks: {multi_domain}")

    print("\nDomain counts:")
    for domain, count in sorted(counts.items()):
        print(f"{domain:12}: {count}")

    print(f"\nSaved to: {OUTPUT}")


if __name__ == "__main__":
    main()
