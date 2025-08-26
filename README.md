# podkeet

Download a YouTube video's audio as MP3 with yt-dlp and transcribe it using Parakeet-MLX on Apple Silicon.

Requirements
- macOS on Apple Silicon (M1/M2/M3)
– Python >= 3.13
- ffmpeg (for yt-dlp post-processing)
  - Install on macOS: `brew install ffmpeg`
- MLX-compatible environment (Parakeet-MLX)

Quick start (uv)
1) Create a virtual environment and install dependencies:

```fish
uv venv --python 3.13
uv pip install -e .
```

2) Use the CLI:

```fish
podkeet transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --out-dir ./outputs
```

This will:
- Check for `ffmpeg` and instruct you to install it if missing.
- Download the best audio stream and convert it to MP3.
- Transcribe the MP3 with Parakeet-MLX, saving a `.txt` transcript next to the audio (and in `--out-dir`).

CLI reference
- podkeet download URL --out-dir PATH
- podkeet transcribe URL_OR_FILE --out-dir PATH [--keep-audio] [--language auto|en|…] [--model NAME] [--format txt|srt|vtt|json] [--device auto|mps|cpu] [-v]
- podkeet pipeline URL --out-dir PATH [same flags as transcribe]

Notes
- If `ffmpeg` is missing, you'll see instructions to install it.
- The first transcription may download Parakeet-MLX models; subsequent runs use the cache.
- On Apple Silicon, `device=auto` prefers MLX (mps) and falls back to CPU if needed.
 - Timing: The CLI shows elapsed time for both download and transcription to help you estimate performance.

Robustness
- Filenames with special characters: We detect the actual file written by yt-dlp post-processing instead of guessing by title, avoiding path mismatches.
- Large files / memory: If a full-file transcription hits a Metal/MLX memory error, the tool automatically falls back to chunked transcription (~10-minute segments) and merges results with correct timestamps.
- Network hiccups: The downloader uses retries, socket timeouts, and exponential backoff to handle transient YouTube timeouts.

Examples
```fish
# Download only
podkeet download "https://www.youtube.com/watch?v=8P7v1lgl-1s" --out-dir ./podcasts

# Transcribe from URL with start at 121 seconds (yt-dlp handles t=)
podkeet transcribe "https://www.youtube.com/watch?v=8P7v1lgl-1s&t=121s" --out-dir ./podcasts

# Transcribe a local file
podkeet transcribe ./podcasts/example.mp3 --out-dir ./podcasts --format srt
```

Developer notes
- Format with Ruff:
  ```fish
  uvx ruff format
  ```
- Lint with Ruff:
  ```fish
  uvx ruff check
  uvx ruff check --fix
  ```
- Type-check with Ty (pre-release):
  ```fish
  uvx ty check
  ```

