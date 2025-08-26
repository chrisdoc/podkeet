from __future__ import annotations
import shutil

from rich.panel import Panel
from rich.text import Text


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
