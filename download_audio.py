
import json
import subprocess
from pathlib import Path

AUDIO_DIR = Path("data/audio")
FAILURE_FILE = Path("data/download_failures.json")

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

with open("videos.json", encoding="utf-8") as f:
    videos = json.load(f)

failed = []

for index, video in enumerate(videos, 1):

    video_id = video["video_id"]
    title = video["title"]

    # Skip already downloaded videos
    existing = [
        p for p in AUDIO_DIR.glob(f"{video_id}.*")
        if p.is_file()
        and not p.name.endswith((".part", ".ytdl", ".tmp"))
    ]

    if existing and existing[0].stat().st_size > 0:
        print(
            f"[{index}/{len(videos)}] Already downloaded: {title}",
            flush=True
        )
        continue

    print(
        f"\n[{index}/{len(videos)}] Downloading: {title}",
        flush=True
    )

    command = [
        "yt-dlp",
        "--no-playlist",
        "--no-overwrites",
        "--retries", "5",
        "--fragment-retries", "5",
        "-f", "bestaudio/best",
        "-o", str(AUDIO_DIR / "%(id)s.%(ext)s"),
        video["url"]
    ]

    try:
        result = subprocess.run(command)

        downloaded = [
            p for p in AUDIO_DIR.glob(f"{video_id}.*")
            if p.is_file()
            and not p.name.endswith((".part", ".ytdl", ".tmp"))
            and p.stat().st_size > 0
        ]

        if result.returncode != 0 or not downloaded:
            print(f"FAILED: {video_id}", flush=True)
            failed.append(video_id)
        else:
            print(f"SUCCESS: {video_id}", flush=True)

    except Exception as e:
        print(f"ERROR: {video_id}: {e}", flush=True)
        failed.append(video_id)

    # Save progress after every video
    FAILURE_FILE.write_text(
        json.dumps(failed, indent=2),
        encoding="utf-8"
    )

print("\nDownload process finished.")
print(f"Failed downloads: {len(failed)}")
