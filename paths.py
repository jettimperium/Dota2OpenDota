from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths

APP_NAME = "Dota2Pulse"
APP_TITLE = "Dota 2 Pulse"
APP_VERSION = "1.2.1"


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    if not location:
        location = str(Path.home() / f".{APP_NAME.lower()}")
    return _ensure(Path(location))


def cache_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
    if not location:
        location = str(Path.home() / f".{APP_NAME.lower()}" / "cache")
    return _ensure(Path(location))


def log_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not base:
        base = str(Path.home() / f".{APP_NAME.lower()}")
    return _ensure(Path(base) / "logs")


def settings_file() -> Path:
    return config_dir() / "settings.ini"


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative
