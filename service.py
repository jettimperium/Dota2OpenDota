from __future__ import annotations

import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from data_tools import DashboardData, MatchWards, build_dashboard, build_match_wards
from dota_api import (
    get_hero_stats,
    get_heroes,
    get_match_details,
    get_player_info,
    get_recent_matches,
    request_match_parse,
)

_heroes_cache: list[dict] | None = None


class ProfileUnavailableError(RuntimeError):
    pass


def load_hero_constants(force: bool = False) -> list[dict]:
    global _heroes_cache
    if _heroes_cache and not force:
        return _heroes_cache
    heroes = get_heroes()
    if heroes:
        _heroes_cache = heroes
        return heroes
    return _heroes_cache or []


def fetch_dashboard(account_id: int, progress: Callable[[str], None] | None = None) -> DashboardData:
    report = progress or (lambda _message: None)

    report("Загружаем профиль игрока")
    player = get_player_info(account_id)
    if not player:
        raise ProfileUnavailableError(
            "OpenDota не вернула профиль. Проверьте Steam32 ID, "
            "настройки приватности истории матчей и подключение к интернету."
        )

    report("Загружаем справочник героев")
    heroes = load_hero_constants()

    report("Получаем последние матчи")
    matches = get_recent_matches(account_id, 20)

    report("Считаем статистику героев")
    hero_stats = get_hero_stats(account_id)

    report("Собираем дашборд")
    return build_dashboard(account_id, player, matches, hero_stats, heroes)


class MatchDetailsUnavailableError(RuntimeError):
    pass


def fetch_match_wards(account_id: int, match_id: int) -> MatchWards:
    """Загружает карточку матча и выделяет варды указанного игрока."""
    raw = get_match_details(match_id)
    if not raw:
        raise MatchDetailsUnavailableError(
            "OpenDota не вернула карточку матча. Возможно, матч удалён, "
            "скрыт или API временно недоступна."
        )
    return build_match_wards(account_id, raw)


class MatchWardsLoader(QObject):
    """Фоновая загрузка карточки матча и запрос парсинга."""

    loaded = Signal(int, object)
    failed = Signal(int, str)
    parse_requested = Signal(int, bool, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._request_id = 0
        self._closed = False

    def start(self, account_id: int, match_id: int) -> int:
        self._request_id += 1
        request_id = self._request_id

        def runner() -> None:
            try:
                data = fetch_match_wards(account_id, match_id)
            except MatchDetailsUnavailableError as error:
                self._emit(self.failed, request_id, str(error))
            except Exception as error:  # noqa: BLE001 — граница фонового потока
                self._emit(
                    self.failed,
                    request_id,
                    f"Неожиданная ошибка при загрузке матча: {error}",
                )
            else:
                self._emit(self.loaded, request_id, data)

        threading.Thread(
            target=runner,
            name=f"opendota-match-{request_id}",
            daemon=True,
        ).start()
        return request_id

    def request_parse(self, match_id: int) -> None:
        def runner() -> None:
            try:
                success, message = request_match_parse(match_id)
            except Exception as error:  # noqa: BLE001
                success, message = False, f"Не удалось отправить запрос: {error}"
            self._emit(self.parse_requested, match_id, success, message)

        threading.Thread(
            target=runner,
            name=f"opendota-parse-{match_id}",
            daemon=True,
        ).start()

    def shutdown(self) -> None:
        self._closed = True

    def _emit(self, signal, *args) -> None:
        if self._closed:
            return
        try:
            signal.emit(*args)
        except RuntimeError:
            # Окно могло быть уничтожено во время закрытия приложения.
            pass


class DashboardLoader(QObject):
    """Запускает сетевую загрузку в фоновом daemon-потоке."""

    progress = Signal(int, str)
    loaded = Signal(int, object)
    failed = Signal(int, str)
    finished = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._request_id = 0
        self._closed = False

    def start(self, account_id: int) -> int:
        self._request_id += 1
        request_id = self._request_id

        def runner() -> None:
            try:
                data = fetch_dashboard(
                    account_id,
                    progress=lambda text: self._emit(self.progress, request_id, text),
                )
            except ProfileUnavailableError as error:
                self._emit(self.failed, request_id, str(error))
            except Exception as error:  # noqa: BLE001 — граница фонового потока
                self._emit(
                    self.failed,
                    request_id,
                    f"Неожиданная ошибка при загрузке данных: {error}",
                )
            else:
                self._emit(self.loaded, request_id, data)
            finally:
                self._emit(self.finished, request_id)

        threading.Thread(
            target=runner,
            name=f"opendota-loader-{request_id}",
            daemon=True,
        ).start()
        return request_id

    def shutdown(self) -> None:
        self._closed = True

    def _emit(self, signal, *args) -> None:
        if self._closed:
            return
        try:
            signal.emit(*args)
        except RuntimeError:
            # Окно уже могло быть уничтожено во время закрытия приложения.
            pass
