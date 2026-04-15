import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from podkeet.cli import app, _fmt_duration
from podkeet.ffmpeg_utils import is_video_file, VIDEO_EXTENSIONS


def test_fmt_duration_zero():
    assert _fmt_duration(0.0) == "0.000s"


def test_fmt_duration_seconds_and_ms():
    # 3.045s should render with ms
    assert _fmt_duration(3.045).endswith("3.045s")


def test_fmt_duration_minutes():
    out = _fmt_duration(65.1)
    # Expect something like '1m 05.100s'
    assert out.startswith("1m ") and out.endswith("s")


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])  # exits early via callback
    assert result.exit_code == 0
    # Output like: 'podkeet 0.1.0' or similar
    assert re.search(r"^podkeet\s+\d+\.\d+\.\d+", result.stdout.strip())


def test_is_video_file_known_extensions():
    for ext in [".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv"]:
        assert is_video_file(Path(f"video{ext}")), f"{ext} should be detected as video"


def test_is_video_file_audio_not_video():
    assert not is_video_file(Path("audio.mp3"))
    assert not is_video_file(Path("audio.wav"))
    assert not is_video_file(Path("document.txt"))


def test_video_extensions_set():
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".mkv" in VIDEO_EXTENSIONS


def test_transcribe_video_file_extracts_audio(tmp_path):
    """Video local files should trigger audio extraction before transcription."""
    runner = CliRunner()
    fake_video = tmp_path / "clip.mp4"
    fake_video.write_bytes(b"fake video content")
    fake_mp3 = tmp_path / "clip.mp3"
    fake_mp3.write_bytes(b"fake mp3 content")  # simulate extracted file on disk

    fake_result = MagicMock()
    fake_result.out_path = tmp_path / "clip.txt"
    fake_result.out_path.write_text("hello world", encoding="utf-8")
    fake_result.text = "hello world"

    with (
        patch("podkeet.cli.extract_audio_from_video", return_value=fake_mp3) as mock_extract,
        patch("podkeet.cli.run_transcription", return_value=fake_result) as mock_transcribe,
    ):
        result = runner.invoke(
            app,
            ["transcribe", str(fake_video), "--out-dir", str(tmp_path), "--no-timing"],
        )

    assert result.exit_code == 0, result.output
    mock_extract.assert_called_once_with(fake_video, tmp_path)
    mock_transcribe.assert_called_once()
    # extracted audio should be deleted after transcription (keep_audio=False)
    assert not fake_mp3.exists()


def test_transcribe_video_file_keep_audio(tmp_path):
    """With --keep-audio the extracted MP3 must not be deleted."""
    runner = CliRunner()
    fake_video = tmp_path / "clip.mp4"
    fake_video.write_bytes(b"fake video content")
    fake_mp3 = tmp_path / "clip.mp3"
    fake_mp3.write_bytes(b"fake mp3")  # simulate extracted file existing

    fake_result = MagicMock()
    fake_result.out_path = tmp_path / "clip.txt"
    fake_result.out_path.write_text("hello world", encoding="utf-8")
    fake_result.text = "hello world"

    with (
        patch("podkeet.cli.extract_audio_from_video", return_value=fake_mp3),
        patch("podkeet.cli.run_transcription", return_value=fake_result),
    ):
        result = runner.invoke(
            app,
            [
                "transcribe",
                str(fake_video),
                "--out-dir",
                str(tmp_path),
                "--keep-audio",
                "--no-timing",
            ],
        )

    assert result.exit_code == 0, result.output
    # File must still exist because --keep-audio was passed
    assert fake_mp3.exists()


def test_transcribe_missing_file_returns_exit_2(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["transcribe", str(tmp_path / "nonexistent.mp4")])
    assert result.exit_code == 2
