from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

from rich.panel import Panel
from rich.text import Text

# Video file extensions that require audio extraction before transcription
VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".flv",
    ".wmv",
    ".ts",
    ".mts",
    ".m2ts",
}


def ensure_ffmpeg() -> None:
    """Ensure ffmpeg is available on PATH.

    Raises RuntimeError with user-friendly instructions if missing.
    """
    if shutil.which("ffmpeg"):
        return

    msg = Text()
    msg.append("ffmpeg is required for audio extraction.\n\n", style="bold red")
    msg.append("Install it on macOS with Homebrew:\n", style="bold")
    msg.append("  brew install ffmpeg\n\n", style="green")
    msg.append(
        "After installing, make sure your shell session can see it (restart your terminal if needed).\n"
    )

    raise RuntimeError(Panel(msg, title="Missing dependency: ffmpeg", border_style="red"))


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def is_video_file(path: Path) -> bool:
    """Return True if *path* has a video file extension."""
    return path.suffix.lower() in VIDEO_EXTENSIONS


def extract_audio_from_video(video_path: Path, out_dir: Path) -> Path:
    """Extract audio from a video file and save it as an MP3 in *out_dir*.

    Returns the path to the extracted MP3.
    """
    ensure_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3_path = out_dir / (video_path.stem + ".mp3")
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "2",
        str(mp3_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return mp3_path
