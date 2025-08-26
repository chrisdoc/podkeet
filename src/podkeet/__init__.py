from importlib import metadata
from pathlib import Path
from typing import Optional

from rich.console import Console

__all__ = ["console", "APP_NAME", "get_version", "Outputs"]

console = Console()
APP_NAME = "podkeet"


def get_version() -> str:
    try:
        return metadata.version(APP_NAME)
    except metadata.PackageNotFoundError:
        return "0.0.0+dev"


class Outputs:
    """Utility to resolve output directories and files."""

    def __init__(self, out_dir: Optional[Path] = None) -> None:
        self.base = Path(out_dir) if out_dir else Path.cwd() / "outputs"
        self.base.mkdir(parents=True, exist_ok=True)

    def resolve_audio_path(self, suggested_name: str, ext: str = "mp3") -> Path:
        return self.base / f"{suggested_name}.{ext}"

    def sibling(self, media_path: Path, suffix: str) -> Path:
        return media_path.with_suffix(suffix)
