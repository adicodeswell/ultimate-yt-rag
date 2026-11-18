import json
from pathlib import Path

TRANSCRIPT_DIR = Path("data/transcripts")
OUTPUT = Path("data/chunks/knowledge_base.jsonl")

CHUNK_SIZE = 75
OVERLAP = 15
STEP = CHUNK_SIZE - OVERLAP


def format_time(seconds):
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def main():

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Rebuild the chunk file from scratch
    with open(OUTPUT, "w", encoding="utf-8") as out:

        transcript_files = sorted(TRANSCRIPT_DIR.glob("*.json"))

        print(f"Found {len(transcript_files)} transcripts.")

        total_chunks = 0

        for index, file in enumerate(transcript_files, 1):

            with open(file, encoding="utf-8") as f:
                video = json.load(f)

            segments = video["segments"]
            duration = video["duration"]

            start = 0
            chunk_number = 0

            while start < duration:

                end = min(
                    start + CHUNK_SIZE,
                    duration
                )

                # Select Whisper segments that overlap this chunk
                selected = [
                    segment
                    for segment in segments
                    if (
                        segment["end"] > start
                        and segment["start"] < end
                    )
                ]

                if selected:

                    text = " ".join(
                        segment["text"]
                        for segment in selected
                    ).strip()

                    if text:

                        # Actual speech boundaries inside this chunk
                        source_start = max(
                            start,
                            selected[0]["start"]
                        )

                        source_end = min(
                            end,
                            selected[-1]["end"]
                        )

                        chunk = {
                            "id": f"{video['video_id']}_{chunk_number}",

                            "text": text,

                            "metadata": {
                                "video_id": video["video_id"],
                                "title": video["title"],
                                "playlists": video["playlists"],

                                "timestamp": {
                                    "start": round(source_start, 3),
                                    "end": round(source_end, 3),
                                    "start_formatted": format_time(source_start),
                                    "end_formatted": format_time(source_end)
                                },

                                "url": (
                                    f"{video['url']}"
                                    f"&t={int(source_start)}s"
                                )
                            }
                        }

                        out.write(
                            json.dumps(
                                chunk,
                                ensure_ascii=False
                            ) + "\n"
                        )

                        total_chunks += 1

                start += STEP
                chunk_number += 1

            print(
                f"[{index}/{len(transcript_files)}] "
                f"{video['title']}"
            )

    print("\nChunking complete.")
    print(f"Total chunks: {total_chunks}")
    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":
    main()