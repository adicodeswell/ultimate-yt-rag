
import json
from collections import Counter
from pathlib import Path

INPUT = Path("data/knowledge_v2/knowledge_base.jsonl")

domain_counts = Counter()
seen_ids = set()

total = 0
duplicate_ids = []
missing_domains = []
invalid_metadata = []

with open(INPUT, encoding="utf-8") as f:
    for line_number, line in enumerate(f, 1):
        chunk = json.loads(line)

        chunk_id = chunk.get("id")
        metadata = chunk.get("metadata", {})
        domains = metadata.get("domains")

        total += 1

        if chunk_id in seen_ids:
            duplicate_ids.append(chunk_id)
        seen_ids.add(chunk_id)

        if not domains:
            missing_domains.append(chunk_id)
        elif not isinstance(domains, list):
            invalid_metadata.append(chunk_id)
        else:
            for domain in domains:
                domain_counts[domain] += 1

        if not metadata.get("video_id") or not metadata.get("url"):
            invalid_metadata.append(chunk_id)

print("\n========== VALIDATION ==========")
print(f"Total chunks: {total}")
print(f"Unique IDs: {len(seen_ids)}")
print(f"Duplicate IDs: {len(duplicate_ids)}")
print(f"Missing domains: {len(missing_domains)}")
print(f"Invalid metadata: {len(invalid_metadata)}")

print("\nDomain counts:")
for domain, count in sorted(domain_counts.items()):
    print(f"{domain:12}: {count}")

if (
    total == 25301
    and len(seen_ids) == total
    and not missing_domains
    and not invalid_metadata
):
    print("\nPASS: Knowledge base structure is valid.")
else:
    print("\nFAIL: Inspect the issues above.")
