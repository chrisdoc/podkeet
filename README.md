– Python >= 3.13
# podkeet

Download a YouTube video's audio as MP3 with `yt-dlp` and transcribe it using Parakeet-MLX (MLX on Apple Silicon).

## Requirements
- macOS on Apple Silicon (M1/M2/M3)
- Python `>= 3.13`
- `ffmpeg` (for `yt-dlp` post-processing)
  - Install on macOS: `brew install ffmpeg`

Parakeet-MLX is installed as a dependency and will use MLX (Metal) on Apple Silicon when `device=auto`.

## Quick start (uv)
1) Create a virtual environment and install dependencies:

```fish
uv venv --python 3.13
uv sync --extra dev
```

2) Use the CLI:

```fish
podkeet transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --out-dir ./outputs
```

This will:
- Check for `ffmpeg` and instruct you to install it if missing.
- Download the best audio stream and convert it to MP3.
- Transcribe the MP3 with Parakeet-MLX, saving a transcript next to the audio (and in `--out-dir`).

## Installation (PyPI)
Once released on PyPI, you can install directly:

```fish
uvx pip install -U podkeet
```

## CLI reference
- `podkeet download URL --out-dir PATH [--no-timing]`
- `podkeet transcribe URL_OR_FILE --out-dir PATH [--keep-audio] [--language auto|en|…] [--model NAME] [--format txt|srt|vtt|json] [--device auto|mps|cpu] [--no-timing] [--version]`

Notes:
- If `ffmpeg` is missing, a clear message explains how to install it.
- The first transcription may download Parakeet-MLX models; subsequent runs use the local cache.
- On Apple Silicon, `device=auto` prefers MLX (`mps`) and falls back to CPU if needed.
- Timing: The CLI shows elapsed time for download and transcription; hide with `--no-timing`.
- JSON: When `--format json` is used, the CLI prints a compact JSON summary to stdout (suitable for automation).

## Robustness
- Filenames with special characters: We detect the actual file written by `yt-dlp` instead of guessing by title, avoiding path mismatches.
- Large files / memory: If a full-file transcription hits a Metal/MLX memory error, the tool automatically falls back to chunked transcription (~10-minute segments) and merges results with correct timestamps.
- Network hiccups: The downloader uses retries, socket timeouts, and exponential backoff to handle transient network failures.

## Examples
```fish
# Download only
podkeet download "https://www.youtube.com/watch?v=8P7v1lgl-1s" --out-dir ./podcasts

# Transcribe from URL with a specific start (yt-dlp handles t=)
podkeet transcribe "https://www.youtube.com/watch?v=8P7v1lgl-1s&t=121s" --out-dir ./podcasts

# Transcribe a local file to SRT
podkeet transcribe ./podcasts/example.mp3 --out-dir ./podcasts --format srt

# JSON summary output (includes timings):
podkeet transcribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format json | jq
```

## Development
Install dev extras and set up the environment:

```fish
uv venv --python 3.13
uv sync --extra dev
```

Format with Ruff:
```fish
uvx ruff format
```

Lint with Ruff:
```fish
uvx ruff check
uvx ruff check --fix
```

Type-check with Ty (pre-release):
```fish
uvx ty check
```

Run tests:
```fish
uv run pytest -q
```

Build package (sdist + wheel):
```fish
uvx --from build pyproject-build
ls dist/
```

### CI/CD
- CI (lint, type, tests, build) runs on pushes and PRs.
- Releases are automated:
  - Conventional Commits drive version bumps and `CHANGELOG.md` via Python Semantic Release.
  - A tag `vX.Y.Z` is created on `main`.
  - The Release workflow builds and publishes to PyPI using OIDC (Trusted Publishing).

Commit message hints (Conventional Commits):
- `feat: …` → minor version bump
- `fix: …` → patch version bump
- `feat!: …` or footer `BREAKING CHANGE:` → major version bump

## Troubleshooting
- `ffmpeg` not found: `brew install ffmpeg` (then re-run).
- MLX out-of-memory: The tool will switch to chunked transcription automatically; if still failing, try a smaller model.
- Network or YouTube rate limiting: The downloader retries with backoff; re-run later if persistent.

## License
MIT

