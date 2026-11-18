
import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


# ---------------- CONFIGURATION ----------------

AUDIO_DIR = Path("data/audio")
TRANSCRIPT_DIR = Path("data/transcripts")
FAILURE_FILE = Path("data/transcription_failures.json")

MODEL_NAME = "large-v3-turbo"
DEVICE = "cuda"
COMPUTE_TYPE = "int8_float16"

BEAM_SIZE = 5


# ---------------- FILE UTILITIES ----------------

def save_json_atomic(path, data):
    """Write JSON safely so interrupted writes don't corrupt files."""
    temp_path = path.with_suffix(path.suffix + ".tmp")

    temp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    temp_path.replace(path)


def load_failures():
    if not FAILURE_FILE.exists():
        return {}

    try:
        return json.loads(FAILURE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_failures(failures):
    save_json_atomic(FAILURE_FILE, failures)


def find_audio(video_id):
    files = [
        path for path in AUDIO_DIR.glob(f"{video_id}.*")
        if path.is_file()
        and not path.name.endswith((".part", ".tmp"))
    ]

    return files[0] if files else None


# ---------------- TRANSCRIPTION ----------------

def main(limit=None):

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    FAILURE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open("videos.json", encoding="utf-8") as f:
        videos = json.load(f)

    failures = load_failures()

    print("Loading Whisper model...", flush=True)

    model = WhisperModel(
        MODEL_NAME,
        device=DEVICE,
        compute_type=COMPUTE_TYPE
    )

    print("Whisper model loaded successfully.", flush=True)

    completed = 0
    skipped = 0
    attempted = 0

    try:
        for index, video in enumerate(videos, start=1):

            video_id = video["video_id"]
            title = video["title"]

            output_file = TRANSCRIPT_DIR / f"{video_id}.json"

            # Skip videos already transcribed.
            if output_file.exists():
                skipped += 1
                continue

            # Stop after the requested number of attempts.
            if limit is not None and attempted >= limit:
                break

            attempted += 1

            audio_file = find_audio(video_id)

            if audio_file is None:
                message = "Audio file not found"

                print(
                    f"\n[{index}/{len(videos)}] MISSING: {title}",
                    flush=True
                )

                failures[video_id] = {
                    "title": title,
                    "error": message
                }

                save_failures(failures)
                continue

            print(
                f"\n[{index}/{len(videos)}] Transcribing: {title}",
                flush=True
            )

            try:
                segments, info = model.transcribe(
                    str(audio_file),
                    beam_size=BEAM_SIZE,
                    vad_filter=True,
                    word_timestamps=False
                )

                transcript_segments = []

                # Iterating this generator performs the actual transcription.
                for segment in segments:
                    transcript_segments.append({
                        "start": round(segment.start, 3),
                        "end": round(segment.end, 3),
                        "text": segment.text.strip()
                    })

                if not transcript_segments:
                    raise ValueError("No speech segments detected")

                result = {
                    "video_id": video_id,
                    "title": title,
                    "url": video["url"],
                    "playlists": video.get("playlists", []),
                    "duration": info.duration,
                    "language": info.language,
                    "language_probability": info.language_probability,
                    "segments": transcript_segments
                }

                # Save each completed video immediately.
                save_json_atomic(output_file, result)

                # Remove this video from the failure log if it succeeded.
                failures.pop(video_id, None)
                save_failures(failures)

                completed += 1

                print(
                    f"Saved: {output_file} "
                    f"({len(transcript_segments)} segments)",
                    flush=True
                )

            except Exception as e:

                print(
                    f"ERROR: {video_id}: {e}",
                    flush=True
                )

                failures[video_id] = {
                    "title": title,
                    "error": str(e)
                }

                save_failures(failures)

    except KeyboardInterrupt:
        print("\n\nStopping transcription safely...", flush=True)

    finally:
        save_failures(failures)

        total_transcripts = len(list(TRANSCRIPT_DIR.glob("*.json")))

        print("\n========== SUMMARY ==========", flush=True)
        print(f"Completed this run: {completed}")
        print(f"Already completed/skipped: {skipped}")
        print(f"Attempted this run: {attempted}")
        print(f"Total saved transcripts: {total_transcripts}")
        print(f"Videos with recorded failures: {len(failures)}")
        print("=============================", flush=True)
        print("You can run this script again to continue.", flush=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Resumable YouTube audio transcription"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of untranscribed videos to attempt"
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    main(limit=args.limit)
