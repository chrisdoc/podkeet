from __future__ import annotations
from pathlib import Path
from time import perf_counter
import json
from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel

from . import Outputs, get_version
from .downloader import download_audio
from .ffmpeg_utils import is_url
from .transcriber import transcribe as run_transcription

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="""
Download YouTube audio as MP3 and transcribe it with Parakeet-MLX on Apple Silicon.
""",
)


@app.callback()
def version_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=lambda v: _print_version(v),
        is_eager=True,
        help="Show version and exit",
    ),
):
    pass


def _print_version(v: Optional[bool]) -> Optional[bool]:
    if v:
        rprint(f"podkeet {get_version()}")
        raise typer.Exit(0)
    return None


def _fmt_duration(seconds: float) -> str:
    """Return a compact human-friendly duration like '1h 02m 03.45s'."""
    total_ms = int(seconds * 1000)
    ms = total_ms % 1000
    total_sec = total_ms // 1000
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    if h:
        return f"{h}h {m:02d}m {s:02d}.{ms:03d}s"
    if m:
        return f"{m}m {s:02d}.{ms:03d}s"
    return f"{s}.{ms:03d}s"


@app.command()
def download(
    url: str = typer.Argument(..., help="YouTube video URL"),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir", help="Output directory for MP3"),
    no_timing: bool = typer.Option(False, "--no-timing", help="Hide timing lines in output panel"),
):
    """Download audio as MP3 from a YouTube URL."""
    outputs = Outputs(out_dir)
    t0 = perf_counter()
    mp3_path = download_audio(url, outputs.base)
    elapsed = perf_counter() - t0
    body_lines = [f"Saved MP3 to {mp3_path}"]
    if not no_timing:
        body_lines += ["", f"⏱️  {_fmt_duration(elapsed)}"]
    rprint(Panel.fit("\n".join(body_lines), title="Download complete", border_style="green"))


@app.command("transcribe")
def transcribe(
    source: str = typer.Argument(..., help="YouTube URL or local audio file (.mp3)"),
    out_dir: Optional[Path] = typer.Option(None, "--out-dir", help="Where to store outputs"),
    keep_audio: bool = typer.Option(
        False, "--keep-audio", help="Keep downloaded MP3 when using URL"
    ),
    language: str = typer.Option("auto", "--language", help="Language code or 'auto'"),
    model: str = typer.Option(
        "mlx-community/parakeet-tdt-0.6b-v2",
        "--model",
        help="Parakeet-MLX model repo (Hugging Face)",
    ),
    format: str = typer.Option("txt", "--format", help="Output format: txt|srt|vtt|json"),
    device: str = typer.Option("auto", "--device", help="auto|mps|cpu"),
    no_timing: bool = typer.Option(False, "--no-timing", help="Hide timing lines in output panel"),
):
    """Transcribe from URL or local file."""
    outputs = Outputs(out_dir)

    download_elapsed: Optional[float] = None
    if is_url(source):
        dt0 = perf_counter()
        mp3_path = download_audio(source, outputs.base)
        download_elapsed = perf_counter() - dt0
    else:
        mp3_path = Path(source)
        if not mp3_path.exists():
            rprint(Panel(f"File not found: {mp3_path}", border_style="red"))
            raise typer.Exit(2)

    tt0 = perf_counter()
    result = run_transcription(
        mp3_path,
        model_name=model,
        language=language,
        device=device,
        out_format=format,
        out_dir=outputs.base,
    )
    transcribe_elapsed = perf_counter() - tt0

    # If requesting JSON transcript format, print a JSON summary for automation
    if format.lower() == "json":
        summary = {
            "status": "ok",
            "transcript_path": str(result.out_path),
            "audio_path": str(mp3_path),
            "source": source,
            "model": model,
            "language": language,
            "device": device,
            "transcribe_seconds": transcribe_elapsed,
        }
        if download_elapsed is not None:
            summary["download_seconds"] = download_elapsed
        # Emit compact JSON to stdout (avoid Rich panel for automation)
        print(json.dumps(summary, ensure_ascii=False))
    else:
        details = [f"Transcript saved to {result.out_path}"]
        if not no_timing:
            details += [
                "",
                f"⏱️  Transcribe: {_fmt_duration(transcribe_elapsed)}",
            ]
            if download_elapsed is not None:
                details.append(f"⏬  Download:   {_fmt_duration(download_elapsed)}")
        rprint(Panel.fit("\n".join(details), title="Transcription complete", border_style="green"))

    if is_url(source) and not keep_audio:
        try:
            mp3_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    app()
