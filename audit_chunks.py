
import json
from collections import defaultdict
from pathlib import Path

KNOWLEDGE_DIR = Path("data/knowledge")
ORIGINAL_FILE = Path("data/chunks/knowledge_base.jsonl")


def main():
    domain_map = defaultdict(list)
    domain_counts = {}

    # Read the original knowledge base
    with open(ORIGINAL_FILE, encoding="utf-8") as f:
        original_ids = {
            json.loads(line)["id"]
            for line in f
        }

    # Read all segregated files
    for file in sorted(KNOWLEDGE_DIR.glob("*.jsonl")):
        count = 0

        with open(file, encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                chunk_id = chunk["id"]

                domain_map[chunk_id].append(file.stem)
                count += 1

        domain_counts[file.stem] = count

    # Find chunks appearing in multiple domains
    duplicated = {
        chunk_id: domains
        for chunk_id, domains in domain_map.items()
        if len(domains) > 1
    }

    # Find missing and unexpected IDs
    segregated_ids = set(domain_map)

    missing = original_ids - segregated_ids
    unexpected = segregated_ids - original_ids

    print("\n========== KNOWLEDGE BASE AUDIT ==========")

    print(f"\nOriginal chunks: {len(original_ids)}")
    print(f"Unique segregated chunks: {len(segregated_ids)}")
    print(f"Total segregated entries: {sum(domain_counts.values())}")

    print("\nDomain counts:")
    for domain, count in sorted(domain_counts.items()):
        print(f"{domain:12}: {count}")

    print("\nDuplicate chunks across domains:", len(duplicated))

    print("\nExamples of duplicated chunks:")
    for chunk_id, domains in list(duplicated.items())[:15]:
        print(f"{chunk_id}: {domains}")

    print("\nMissing chunks:", len(missing))
    print("Unexpected chunks:", len(unexpected))

    # Save duplicate report
    report = {
        "original_chunks": len(original_ids),
        "unique_segregated_chunks": len(segregated_ids),
        "total_segregated_entries": sum(domain_counts.values()),
        "domain_counts": domain_counts,
        "duplicate_count": len(duplicated),
        "duplicates": duplicated,
        "missing_count": len(missing),
        "missing_ids": sorted(missing),
        "unexpected_count": len(unexpected),
        "unexpected_ids": sorted(unexpected)
    }

    output = Path("data/chunk_audit.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()
