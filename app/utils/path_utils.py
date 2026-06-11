import sys
import os
from pathlib import Path


def _appdata_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "AYUDIN"


def _bundle_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


def resource_path(relative_path: str) -> str:
    return str(_bundle_dir() / relative_path)


def asset_path(relative: str) -> str:
    return resource_path(os.path.join("app", "assets", relative))


def writable_config_path(filename: str) -> str:
    if getattr(sys, 'frozen', False):
        path = _appdata_dir() / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)
    path = _bundle_dir() / "app" / "config" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)
