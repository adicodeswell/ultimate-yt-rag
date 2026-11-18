
import json
import subprocess
import sys
from pathlib import Path

with open("playlists.json", "r") as f:
    playlists = json.load(f)

videos_by_id = {}

for playlist in playlists:

    print(f"\nProcessing: {playlist['title']}")

    command = [
        sys.executable,
        "-m", "yt_dlp",
        "--flat-playlist",
        "--dump-json",
        "--ignore-errors",
        "--no-warnings",
        playlist["url"]
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    count = 0

    for line in result.stdout.splitlines():

        try:
            video = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(video, dict):
            continue

        video_id = video.get("id")

        if not video_id:
            continue

        if video_id not in videos_by_id:
            videos_by_id[video_id] = {
                "video_id": video_id,
                "title": video.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "playlists": []
            }

        membership = {
            "playlist_id": playlist["playlist_id"],
            "playlist_title": playlist["title"],
            "category": playlist.get("category", ""),
            "level": playlist.get("level", "")
        }

        if membership not in videos_by_id[video_id]["playlists"]:
            videos_by_id[video_id]["playlists"].append(membership)

        count += 1

    if count == 0:
        print("WARNING: No videos extracted.")
        print("yt-dlp error:", result.stderr[-1000:])
    else:
        print(f"Extracted {count} videos.")

videos = list(videos_by_id.values())

Path("data").mkdir(exist_ok=True)

with open("videos.json", "w") as f:
    json.dump(videos, f, indent=2, ensure_ascii=False)

print("\n----------------------------")
print(f"Total unique videos: {len(videos)}")
print("Saved to videos.json")
