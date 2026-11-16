from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings

from paths import settings_file

VALID_ACCENTS = {"emerald", "amber", "crimson"}


@dataclass(slots=True)
class AppConfig:
    account_id: int | None = None
    accent: str = "emerald"


class ConfigStore:
    """Небольшая обёртка над QSettings с INI-файлом в AppData."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_file()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = QSettings(str(self.path), QSettings.Format.IniFormat)

    def load(self) -> AppConfig:
        raw_account = self._settings.value("account/id", "", type=str)
        account_id: int | None = None
        if raw_account:
            try:
                candidate = int(raw_account)
                if 1 <= candidate <= 4_294_967_295:
                    account_id = candidate
            except (TypeError, ValueError):
                account_id = None

        accent = self._settings.value("appearance/accent", "emerald", type=str)
        if accent not in VALID_ACCENTS:
            accent = "emerald"

        return AppConfig(account_id=account_id, accent=accent)

    def save(self, config: AppConfig) -> None:
        if config.account_id is None:
            self._settings.remove("account/id")
        else:
            self._settings.setValue("account/id", str(config.account_id))
        self._settings.setValue("appearance/accent", config.accent)
        self._settings.sync()

    def save_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue("window/geometry", geometry)
        self._settings.sync()

    def restore_geometry(self) -> QByteArray:
        value = self._settings.value("window/geometry")
        return value if isinstance(value, QByteArray) else QByteArray()

    def sync(self) -> None:
        self._settings.sync()
