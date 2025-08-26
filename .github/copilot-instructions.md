# Copilot Instructions for podkeet

This repo is a Python 3.13 CLI that downloads YouTube audio to MP3 via `yt-dlp` and transcribes it with Parakeet-MLX on Apple Silicon. The CLI is built with Typer and Rich, uses `uv` for env/build tooling, and ships automated CI/CD with GitHub Actions, semantic versioning, and Trusted Publishing to PyPI.

## Architecture and Key Modules
- CLI entry: `src/podkeet/cli.py`
  - Commands: `download` (URL → MP3) and `transcribe` (URL or local file → transcript).
  - Shows timing by default; suppress with `--no-timing`. When `--format json`, prints a JSON summary to stdout.
  - Version via `--version` reads package metadata (`get_version`).
- Downloader: `src/podkeet/downloader.py`
  - Uses `yt-dlp` + `ffmpeg` to fetch best audio and convert to MP3.
  - Robust MP3 path detection: prefers `requested_downloads` filepaths; otherwise diffs directory state and picks the most recent `.mp3`.
  - Retries with exponential backoff on flaky networks.
- Transcriber: `src/podkeet/transcriber.py`
  - Uses `parakeet-mlx` with MLX; default model `mlx-community/parakeet-tdt-0.6b-v2`.
  - Fallback on MLX OOM: splits audio into ~10-minute chunks with `ffmpeg`, transcribes sequentially, offsets/merges timestamps, then formats to `txt|srt|vtt|json`.
  - `ffprobe` determines segment durations to compute accurate offsets.
- FFmpeg utils: `src/podkeet/ffmpeg_utils.py`
  - `ensure_ffmpeg()` raises a helpful error panel if `ffmpeg` is missing.
  - `is_url()` utility used by CLI.
- Package utils: `src/podkeet/__init__.py`
  - `get_version()` returns installed package version or `0.0.0+dev` for local.
  - `Outputs` helper ensures an `outputs/` directory and resolves sibling paths.

## Tooling and Developer Workflows
- Python: `>= 3.13`. Use `uv` for env and tooling.
- Install dev env:
  - `uv venv --python 3.13`
  - `uv sync --extra dev`
- Format/Lint/Types:
  - `uvx ruff format`
  - `uvx ruff check` (optionally `--fix`)
  - `uvx ty check`
- Tests: `uv run pytest -q`
- Build package: `uvx --from build pyproject-build` → artifacts in `dist/`.
- Run CLI:
  - `podkeet download URL --out-dir PATH`
  - `podkeet transcribe URL_OR_FILE --out-dir PATH [--format txt|srt|vtt|json] [--device auto|mps|cpu] [--language auto|en] [--keep-audio] [--no-timing]`

## CI/CD and Releases
- CI workflow (`.github/workflows/ci.yml`): ruff, ty, pytest, build, and dist artifacts.
- Automated versioning (`.github/workflows/versioning.yml`):
  - Conventional Commits drive Python Semantic Release.
  - Runs `semantic-release version` with `GITHUB_TOKEN`, updates version (`version_toml`), generates `CHANGELOG.md`.
  - Pushes commit and annotated tag with `--follow-tags`.
  - Dispatches the Release workflow with the new tag using `gh workflow run`.
- Release workflow (`.github/workflows/release.yml`):
  - Triggers on tag pushes `v*.*.*` and manual dispatch (with optional `tag` input).
  - On dispatch, checks out the provided tag, builds with `uvx --from build pyproject-build`, uploads `dist`, and publishes to PyPI with OIDC.

## Conventions and Tips
- Prefer `uv` for everything (env, running, and building). Avoid `pip install` directly unless stated.
- The CLI prints Rich panels for humans; when scripting, use `--format json` to get machine-readable output and avoid Rich panels.
- Assume Apple Silicon/MLX by default; the transcriber will fallback to CPU if MLX is unavailable.
- When changing downloader behavior, keep the robust MP3 detection logic and retries.
- When modifying transcription formatting, update corresponding helper functions in `transcriber.py` and ensure timestamps remain accurate after chunk merging.

## Key Files
- `pyproject.toml` – project metadata, dependencies, dev extras, and semantic-release config.
- `README.md` – describes usage, development, CI/CD, and troubleshooting.
- `.github/workflows/*` – CI (`ci.yml`), versioning (`versioning.yml`), and release (`release.yml`).

## Example patterns
- JSON automation output:
  - `podkeet transcribe "<url-or-file>" --format json | jq`
- Handling missing ffmpeg:
  - `ensure_ffmpeg()` raises a user-friendly Rich panel; tests/CLI should surface this clearly.

If anything here is unclear or if additional conventions should be captured (e.g., preferred model names, chunk sizes, or CI job tweaks), let me know and I’ll refine this document.
