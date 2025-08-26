import re
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
