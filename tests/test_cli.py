import re
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner

from podkeet.cli import app, _fmt_duration


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


def test_transcribe_stdout_option():
    """Test that --stdout option outputs transcript content to stdout."""
    runner = CliRunner()
    
    # Create a mock result that would be returned by the transcriber
    mock_result = MagicMock()
    mock_result.formatted_content = "This is a test transcript."
    mock_result.out_path = Path("/tmp/test.txt")
    mock_result.text = "This is a test transcript."
    
    # Mock the transcriber function to return our mock result
    with patch('podkeet.cli.run_transcription') as mock_transcribe, \
         patch('podkeet.cli.is_url') as mock_is_url, \
         patch('pathlib.Path.exists') as mock_exists:
        
        mock_transcribe.return_value = mock_result
        mock_is_url.return_value = False  # Treat as local file
        mock_exists.return_value = True  # File exists
        
        # Test with --stdout option
        result = runner.invoke(app, ["transcribe", "test.mp3", "--stdout"])
        
        # Should output transcript content to stdout
        assert result.exit_code == 0
        assert "This is a test transcript." in result.stdout
        # Should not contain Rich panel formatting when using stdout
        assert "Transcript saved to" not in result.stdout


def test_transcribe_stdout_with_format():
    """Test that --stdout works with different formats."""
    runner = CliRunner()
    
    # Create a mock result with SRT formatted content
    mock_result = MagicMock()
    mock_result.formatted_content = "1\n00:00:00,000 --> 00:00:05,000\nTest transcript\n\n"
    mock_result.out_path = Path("/tmp/test.srt")
    mock_result.text = "Test transcript"
    
    with patch('podkeet.cli.run_transcription') as mock_transcribe, \
         patch('podkeet.cli.is_url') as mock_is_url, \
         patch('pathlib.Path.exists') as mock_exists:
        
        mock_transcribe.return_value = mock_result
        mock_is_url.return_value = False
        mock_exists.return_value = True
        
        # Test with --stdout and --format srt
        result = runner.invoke(app, ["transcribe", "test.mp3", "--stdout", "--format", "srt"])
        
        assert result.exit_code == 0
        assert "00:00:00,000 --> 00:00:05,000" in result.stdout
        assert "Test transcript" in result.stdout
