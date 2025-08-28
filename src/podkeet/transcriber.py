from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
import subprocess
import tempfile
from typing import Tuple
from pathlib import Path
from typing import Optional, Any, Dict, List

from rich.console import Console

from .ffmpeg_utils import ensure_ffmpeg

console = Console()


# Local copies of formatters inspired by parakeet_mlx.cli
# to avoid depending on internal CLI module.


def _format_timestamp(
    seconds: float, always_include_hours: bool = True, decimal_marker: str = ","
) -> str:
    assert seconds >= 0
    milliseconds = round(seconds * 1000.0)
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    sec = milliseconds // 1_000
    milliseconds %= 1_000
    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{sec:02d}{decimal_marker}{milliseconds:03d}"


def _to_txt(result: Any) -> str:
    return (getattr(result, "text", "") or "").strip()


def _to_srt(result: Any, highlight_words: bool = False) -> str:
    srt_content: List[str] = []
    entry_index = 1
    sentences = getattr(result, "sentences", [])
    if highlight_words:
        for sentence in sentences:
            tokens = getattr(sentence, "tokens", [])
            for i, token in enumerate(tokens):
                start_time = _format_timestamp(getattr(token, "start", 0.0), decimal_marker=",")
                end_val = (
                    getattr(token, "end", 0.0)
                    if i == len(tokens) - 1
                    else getattr(tokens[i + 1], "start", 0.0)
                )
                end_time = _format_timestamp(end_val, decimal_marker=",")
                text = ""
                for j, inner_token in enumerate(tokens):
                    ttxt = getattr(inner_token, "text", "")
                    if i == j:
                        text += ttxt.replace(ttxt.strip(), f"<u>{ttxt.strip()}</u>")
                    else:
                        text += ttxt
                text = text.strip()
                srt_content.append(str(entry_index))
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(text)
                srt_content.append("")
                entry_index += 1
    else:
        for sentence in sentences:
            start_time = _format_timestamp(getattr(sentence, "start", 0.0), decimal_marker=",")
            end_time = _format_timestamp(getattr(sentence, "end", 0.0), decimal_marker=",")
            text = (getattr(sentence, "text", "") or "").strip()
            srt_content.append(str(entry_index))
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")
            entry_index += 1
    return "\n".join(srt_content)


def _to_vtt(result: Any, highlight_words: bool = False) -> str:
    vtt_content: List[str] = ["WEBVTT", ""]
    sentences = getattr(result, "sentences", [])
    if highlight_words:
        for sentence in sentences:
            tokens = getattr(sentence, "tokens", [])
            for i, token in enumerate(tokens):
                start_time = _format_timestamp(getattr(token, "start", 0.0), decimal_marker=".")
                end_val = (
                    getattr(token, "end", 0.0)
                    if i == len(tokens) - 1
                    else getattr(tokens[i + 1], "start", 0.0)
                )
                end_time = _format_timestamp(end_val, decimal_marker=".")
                text_line = ""
                for j, inner_token in enumerate(tokens):
                    ttxt = getattr(inner_token, "text", "")
                    if i == j:
                        text_line += ttxt.replace(ttxt.strip(), f"<b>{ttxt.strip()}</b>")
                    else:
                        text_line += ttxt
                text_line = text_line.strip()
                vtt_content.append(f"{start_time} --> {end_time}")
                vtt_content.append(text_line)
                vtt_content.append("")
    else:
        for sentence in sentences:
            start_time = _format_timestamp(getattr(sentence, "start", 0.0), decimal_marker=".")
            end_time = _format_timestamp(getattr(sentence, "end", 0.0), decimal_marker=".")
            text_line = (getattr(sentence, "text", "") or "").strip()
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(text_line)
            vtt_content.append("")
    return "\n".join(vtt_content)


def _to_json(result: Any) -> str:
    import json

    def token_to_dict(tok: Any) -> Dict[str, Any]:
        return {
            "text": getattr(tok, "text", ""),
            "start": round(float(getattr(tok, "start", 0.0)), 3),
            "end": round(float(getattr(tok, "end", 0.0)), 3),
            "duration": round(float(getattr(tok, "duration", 0.0)), 3),
        }

    def sentence_to_dict(sent: Any) -> Dict[str, Any]:
        tokens = [token_to_dict(t) for t in getattr(sent, "tokens", [])]
        return {
            "text": getattr(sent, "text", ""),
            "start": round(float(getattr(sent, "start", 0.0)), 3),
            "end": round(float(getattr(sent, "end", 0.0)), 3),
            "duration": round(float(getattr(sent, "duration", 0.0)), 3),
            "tokens": tokens,
        }

    output_dict = {
        "text": getattr(result, "text", ""),
        "sentences": [sentence_to_dict(s) for s in getattr(result, "sentences", [])],
    }
    return json.dumps(output_dict, indent=2, ensure_ascii=False)


def _result_to_dict(result: Any) -> Dict[str, Any]:
    """Normalize a parakeet result to a plain Python dict we can manipulate."""

    def token_to_dict(tok: Any) -> Dict[str, Any]:
        return {
            "text": getattr(tok, "text", ""),
            "start": float(getattr(tok, "start", 0.0)),
            "end": float(getattr(tok, "end", 0.0)),
            "duration": float(getattr(tok, "duration", 0.0)),
        }

    def sentence_to_dict(sent: Any) -> Dict[str, Any]:
        tokens = [token_to_dict(t) for t in getattr(sent, "tokens", [])]
        return {
            "text": getattr(sent, "text", ""),
            "start": float(getattr(sent, "start", 0.0)),
            "end": float(getattr(sent, "end", 0.0)),
            "duration": float(getattr(sent, "duration", 0.0)),
            "tokens": tokens,
        }

    return {
        "text": getattr(result, "text", ""),
        "sentences": [sentence_to_dict(s) for s in getattr(result, "sentences", [])],
    }


def _dict_with_offset(d: Dict[str, Any], offset: float) -> Dict[str, Any]:
    """Apply a time offset (seconds) to all timings in a normalized result dict."""
    out = {
        "text": d.get("text", ""),
        "sentences": [],
    }
    for s in d.get("sentences", []):
        ss = {
            "text": s.get("text", ""),
            "start": s.get("start", 0.0) + offset,
            "end": s.get("end", 0.0) + offset,
            "duration": s.get("duration", 0.0),
            "tokens": [],
        }
        for t in s.get("tokens", []):
            ss["tokens"].append(
                {
                    "text": t.get("text", ""),
                    "start": t.get("start", 0.0) + offset,
                    "end": t.get("end", 0.0) + offset,
                    "duration": t.get("duration", 0.0),
                }
            )
        out["sentences"].append(ss)
    return out


def _merge_result_dicts(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple normalized result dicts into one."""
    text: List[str] = []
    sentences: List[Dict[str, Any]] = []
    for p in parts:
        t = (p.get("text") or "").strip()
        if t:
            text.append(t)
        sentences.extend(p.get("sentences", []))
    return {"text": "\n\n".join(text), "sentences": sentences}


def _ns(obj: Any) -> Any:
    """Recursively convert dicts to SimpleNamespace to satisfy getattr in formatters."""
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_ns(x) for x in obj]
    return obj


def _ffprobe_duration(path: Path) -> float:
    """Get duration in seconds using ffprobe. Returns 0.0 on failure."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            stderr=subprocess.STDOUT,
        )
        return float(out.decode("utf-8").strip())
    except Exception:
        return 0.0


def _split_audio(input_path: Path, chunk_seconds: int = 600) -> Tuple[List[Path], List[float]]:
    """Split input audio into roughly chunk_seconds parts using ffmpeg segmenter.

    Returns list of segment paths and their durations.
    """
    with tempfile.TemporaryDirectory(prefix="podkeet-seg-") as tmpdir:
        # Keep directory around by copying paths out after segmentation
        temp_dir = Path(tmpdir)
        pattern = temp_dir / "part-%05d.mp3"
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-i",
            str(input_path),
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-c",
            "copy",
            str(pattern),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        parts = sorted(temp_dir.glob("part-*.mp3"))
        # Copy parts to a stable temp folder we return (since TemporaryDirectory will be deleted)
        # Instead, we move them to a new temp dir that persists for the caller lifetime
        persist = Path(tempfile.mkdtemp(prefix="podkeet-parts-"))
        out_paths: List[Path] = []
        durations: List[float] = []
        for p in parts:
            dst = persist / p.name
            p.replace(dst)
            out_paths.append(dst)
            durations.append(_ffprobe_duration(dst))
        return out_paths, durations


@dataclass
class TranscriptionResult:
    text: str
    out_path: Path
    formatted_content: str


def transcribe(
    audio_path: Path,
    *,
    model_name: str = "mlx-community/parakeet-tdt-0.6b-v2",
    language: str = "auto",
    device: str = "auto",
    out_format: str = "txt",
    out_dir: Optional[Path] = None,
) -> TranscriptionResult:
    """Transcribe the given audio file using Parakeet-MLX.

    Downloads the model if missing via from_pretrained and writes output in
    the requested format.
    """
    ensure_ffmpeg()  # required by parakeet_mlx.audio.load_audio

    try:
        from parakeet_mlx import from_pretrained
        from mlx.core import bfloat16
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "parakeet-mlx is not installed. Install it with:\n"
            "  uv pip install parakeet-mlx\n"
            "or\n"
            "  pip install parakeet-mlx"
        ) from e

    # Load model (dtype bfloat16 by default; parakeet-mlx uses MLX backend)
    model = from_pretrained(model_name, dtype=bfloat16)

    # Ensure output path
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / (audio_path.stem + f".{out_format}")
    else:
        out_path = audio_path.with_suffix(f".{out_format}")

    # Try full-file transcription first. If MLX runs out of memory, fall back to chunking.
    try:
        result = model.transcribe(audio_path)
    except Exception as e:
        msg = str(e)
        if "metal::malloc" in msg or "maximum allowed buffer size" in msg:
            # Fallback: chunked transcription
            parts, durations = _split_audio(audio_path, chunk_seconds=600)
            results: List[Dict[str, Any]] = []
            offset = 0.0
            for idx, part in enumerate(parts):
                r = model.transcribe(part)
                rd = _result_to_dict(r)
                results.append(_dict_with_offset(rd, offset))
                # advance offset by exact segment duration if available
                seg_dur = durations[idx] if idx < len(durations) else 0.0
                offset += seg_dur if seg_dur > 0 else 600.0
            merged = _merge_result_dicts(results)
            result = _ns(merged)
            # chunked fallback executed
        else:
            raise

    formatters = {
        "txt": _to_txt,
        "srt": lambda r: _to_srt(r, highlight_words=False),
        "vtt": lambda r: _to_vtt(r, highlight_words=False),
        "json": _to_json,
    }
    if out_format not in formatters:
        raise ValueError(f"Unsupported format: {out_format}. Choose from txt|srt|vtt|json")

    content = formatters[out_format](result)
    out_path.write_text(content, encoding="utf-8")

    return TranscriptionResult(text=_to_txt(result), out_path=out_path, formatted_content=content)
