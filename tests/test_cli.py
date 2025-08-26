import re
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import MagicMock

from podkeet.cli import app, _fmt_duration
from podkeet.transcriber import TranscriptionResult

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


def test_transcribe_to_file(mocker, tmp_path: Path):
    runner = CliRunner()
    mock_run_transcription = mocker.patch(
        "podkeet.cli.run_transcription",
        return_value=TranscriptionResult(
            content="test transcription",
            format="txt",
            out_path=tmp_path / "test.txt",
        ),
    )
    # Create a dummy audio file
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()

    result = runner.invoke(app, ["transcribe", str(audio_file), "--out-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Transcript saved to" in result.stdout
    assert (tmp_path / "test.txt").exists()
    assert (tmp_path / "test.txt").read_text() == "test transcription"
    mock_run_transcription.assert_called_once()


def test_transcribe_to_stdout(mocker, tmp_path: Path):
    runner = CliRunner()
    mock_run_transcription = mocker.patch(
        "podkeet.cli.run_transcription",
        return_value=TranscriptionResult(
            content="test transcription",
            format="txt",
            out_path=tmp_path / "test.txt",
        ),
    )
    # Create a dummy audio file
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()

    result = runner.invoke(app, ["transcribe", str(audio_file), "--stdout"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "test transcription"
    assert not (tmp_path / "test.txt").exists()
    mock_run_transcription.assert_called_once()

def test_transcribe_json_to_file(mocker, tmp_path: Path):
    runner = CliRunner()
    mock_run_transcription = mocker.patch(
        "podkeet.cli.run_transcription",
        return_value=TranscriptionResult(
            content='{"text": "test"}',
            format="json",
            out_path=tmp_path / "test.json",
        ),
    )
    # Create a dummy audio file
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()

    result = runner.invoke(app, ["transcribe", str(audio_file), "--format", "json", "--out-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "transcript_path" in result.stdout
    assert (tmp_path / "test.json").exists()
    assert (tmp_path / "test.json").read_text() == '{"text": "test"}'
    mock_run_transcription.assert_called_once()


def test_transcribe_json_to_stdout(mocker, tmp_path: Path):
    runner = CliRunner()
    mock_run_transcription = mocker.patch(
        "podkeet.cli.run_transcription",
        return_value=TranscriptionResult(
            content='{"text": "test"}',
            format="json",
            out_path=tmp_path / "test.json",
        ),
    )
    # Create a dummy audio file
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()

    result = runner.invoke(app, ["transcribe", str(audio_file), "--format", "json", "--stdout"])

    assert result.exit_code == 0
    assert result.stdout.strip() == '{"text": "test"}'
    assert not (tmp_path / "test.json").exists()
    mock_run_transcription.assert_called_once()
