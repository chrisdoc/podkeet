from __future__ import annotations

from pathlib import Path
from typing import List
import time

from .ffmpeg_utils import ensure_ffmpeg


class YTDLPLogger:
    def debug(self, msg: str) -> None:  # yt-dlp calls this
        pass

    def warning(self, msg: str) -> None:  # yt-dlp calls this
        pass

    def error(self, msg: str) -> None:  # yt-dlp calls this
        pass


def download_audio(url: str, output_dir: Path) -> Path:
    """Download best audio from a YouTube URL and convert to MP3.

    Returns the final MP3 file path.
    """
    ensure_ffmpeg()

    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "logger": YTDLPLogger(),
        "noprogress": True,
        "quiet": True,
        # Improve robustness on flaky networks
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
    }

    # Capture directory snapshot to robustly locate the newly created MP3
    before: List[Path] = list(output_dir.glob("*"))
    before_names = {p.name for p in before}
    start_time = time.time()

    with YoutubeDL(ydl_opts) as ydl:
        for attempt in range(5):
            try:
                info = ydl.extract_info(url, download=True)
                break
            except DownloadError:
                if attempt == 4:
                    raise
                # exponential backoff
                time.sleep(2**attempt)

    # Prefer explicit filepath from yt-dlp if present
    # Many yt-dlp versions populate requested_downloads with final filepaths
    candidates: List[Path] = []
    try:
        reqs = info.get("requested_downloads") or []
        for req in reqs:
            fp = req.get("filepath") or req.get("_filename") or req.get("filename")
            if fp:
                p = Path(fp)
                if p.suffix.lower() == ".mp3" and p.exists():
                    candidates.append(p)
    except Exception:
        pass

    # Fall back to diffing directory contents created during this call
    if not candidates:
        after = list(output_dir.glob("*.mp3"))
        new_files = [p for p in after if p.name not in before_names]
        # If nothing obvious, also consider files modified very recently
        if not new_files:
            recent = [p for p in after if p.stat().st_mtime >= start_time - 2]
            new_files = recent
        # If multiple, pick the most recent
        if new_files:
            candidates = sorted(new_files, key=lambda p: p.stat().st_mtime, reverse=True)

    if candidates:
        return candidates[0]

    # Last resort: guess from title (may fail if yt-dlp sanitized differently)
    title = info.get("title") or "audio"
    guessed = output_dir / f"{title}.mp3"
    return guessed
