from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import AppConfig, ConfigStore
from data_tools import DashboardData
from image_provider import ImageProvider
from pages import HeroesPage, MatchesPage, OverviewPage, scroll_page
from paths import APP_TITLE, APP_VERSION
from service import DashboardLoader
from settings_dialog import SettingsDialog
from theme import apply_theme
from wards import WardsPage
from widgets import ErrorPage, LoadingPage, LogoMark, NavButton, Toast


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: AppConfig,
        store: ConfigStore,
        initial_data: DashboardData | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._store = store
        self._data: DashboardData | None = None
        self._pages: list[QWidget] = []
        self._current_page = 0
        self._active_request = 0
        self._loading = False
        self._closing = False
        self._last_update = ""

        self.setMinimumSize(1024, 640)
        self._set_initial_geometry()
        self.setWindowTitle(APP_TITLE)

        self._provider = ImageProvider(self)
        self._loader = DashboardLoader(self)
        self._loader.progress.connect(self._on_loader_progress)
        self._loader.loaded.connect(self._on_loader_loaded)
        self._loader.failed.connect(self._on_loader_failed)
        self._loader.finished.connect(self._on_loader_finished)

        self._build_ui()
        self._shortcuts = [
            QShortcut(QKeySequence("F5"), self, activated=self.refresh_data),
            QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings),
        ]

        if initial_data is not None:
            self._data = initial_data
            self._render_data()
        elif autoload:
            QTimer.singleShot(120, self.refresh_data)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self._central = central
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_nav())

        self._loader_bar = QProgressBar()
        self._loader_bar.setObjectName("ThinLoader")
        self._loader_bar.setTextVisible(False)
        self._loader_bar.setRange(0, 1)
        self._loader_bar.setValue(0)
        self._loader_bar.setFixedHeight(2)
        root.addWidget(self._loader_bar)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        self._loading_page = LoadingPage()
        self._error_page = ErrorPage()
        self._error_page.retry_requested.connect(self.refresh_data)
        self._error_page.settings_requested.connect(self.open_settings)
        self._stack.addWidget(self._loading_page)
        self._stack.addWidget(self._error_page)
        self._stack.setCurrentWidget(self._loading_page)

        root.addWidget(self._build_footer())

        self._toast = Toast(central)
        self._toast.hide()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        header.setFixedHeight(70)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(12)

        layout.addWidget(LogoMark(38))
        brand = QVBoxLayout()
        brand.setSpacing(0)
        title = QLabel("DOTA 2 PULSE")
        title.setObjectName("AppTitle")
        brand.addWidget(title)
        subtitle = QLabel("PROFILE INTELLIGENCE")
        subtitle.setObjectName("AppSubtitle")
        brand.addWidget(subtitle)
        layout.addLayout(brand)
        layout.addStretch(1)

        self._status_dot = QLabel()
        self._status_dot.setObjectName("WarningDot")
        self._status_dot.setFixedSize(7, 7)
        layout.addWidget(self._status_dot)

        status_block = QVBoxLayout()
        status_block.setSpacing(0)
        self._status_label = QLabel("Ожидание")
        self._status_label.setObjectName("Muted")
        status_block.addWidget(self._status_label)
        self._status_time = QLabel("OpenDota API")
        self._status_time.setObjectName("Dim")
        status_block.addWidget(self._status_time)
        layout.addLayout(status_block)
        layout.addSpacing(8)

        self._refresh_button = QPushButton("Обновить")
        self._refresh_button.setObjectName("Ghost")
        self._refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_button.setMinimumWidth(108)
        self._refresh_button.clicked.connect(self.refresh_data)
        layout.addWidget(self._refresh_button)

        self._settings_button = QPushButton("Настройки")
        self._settings_button.setObjectName("Ghost")
        self._settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_button.clicked.connect(self.open_settings)
        layout.addWidget(self._settings_button)
        return header

    def _build_nav(self) -> QWidget:
        nav = QWidget()
        nav.setObjectName("NavBar")
        nav.setFixedHeight(53)
        layout = QHBoxLayout(nav)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(2)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[NavButton] = []
        for index, text in enumerate(("Обзор", "Матчи", "Герои", "Варды")):
            button = NavButton(text)
            self._nav_group.addButton(button, index)
            self._nav_buttons.append(button)
            layout.addWidget(button)
        self._nav_buttons[0].setChecked(True)
        self._nav_group.idClicked.connect(self._select_page)
        layout.addStretch(1)

        self._nav_account = QLabel("Steam32 · —")
        self._nav_account.setObjectName("Dim")
        layout.addWidget(self._nav_account)
        return nav

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setObjectName("Footer")
        footer.setFixedHeight(32)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(10)
        left = QLabel("Dota 2 Pulse · данные OpenDota API · не связано с Valve")
        left.setObjectName("Dim")
        layout.addWidget(left)
        layout.addStretch(1)
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("Dim")
        layout.addWidget(version)
        return footer

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def refresh_data(self, force: bool = False) -> None:
        if self._closing:
            return
        if self._config.account_id is None:
            self.open_settings()
            return
        if self._loading and not force:
            return
        self._loading = True
        self._refresh_button.setEnabled(False)
        self._refresh_button.setText("Загрузка…")
        self._loader_bar.setRange(0, 0)
        self._set_status("Загружаем данные…", "warn")
        self._loading_page.set_status("Подключаемся к OpenDota")

        if self._data is None:
            self._stack.setCurrentWidget(self._loading_page)
            self._set_nav_enabled(False)
            self._nav_account.setText(f"Steam32 · {self._config.account_id}")

        self._active_request = self._loader.start(self._config.account_id)

    def _on_loader_progress(self, request_id: int, text: str) -> None:
        if request_id != self._active_request:
            return
        self._loading_page.set_status(text)
        self._set_status(text, "warn")

    def _on_loader_loaded(self, request_id: int, data) -> None:
        if request_id != self._active_request:
            return
        self._loading = False
        self._data = data
        self._render_data()
        self._finish_loading()
        self._set_status("Данные актуальны", "ok")
        now = datetime.now().strftime("%H:%M")
        self._last_update = now
        self._status_time.setText(f"обновлено в {now}")

    def _on_loader_failed(self, request_id: int, message: str) -> None:
        if request_id != self._active_request:
            return
        self._loading = False
        self._finish_loading()
        self._set_status("Ошибка загрузки", "error")
        if self._data is None:
            self._error_page.set_error(message)
            self._stack.setCurrentWidget(self._error_page)
            self._set_nav_enabled(False)
        else:
            self._toast.show_message(f"Не удалось обновить данные. {message}", 5200)

    def _on_loader_finished(self, request_id: int) -> None:
        if request_id != self._active_request:
            return
        self._finish_loading()

    def _finish_loading(self) -> None:
        self._loading = False
        self._loader_bar.setRange(0, 1)
        self._loader_bar.setValue(0)
        self._refresh_button.setEnabled(True)
        self._refresh_button.setText("Обновить")

    # ------------------------------------------------------------------
    # Data rendering
    # ------------------------------------------------------------------
    def _render_data(self) -> None:
        data = self._data
        if data is None:
            return
        self._remove_pages()

        overview = OverviewPage(data, self._provider)
        overview.heroes_requested.connect(lambda: self._select_page(2))
        overview_page = scroll_page(overview)
        matches_page = MatchesPage(data, self._provider)
        heroes_page = scroll_page(HeroesPage(data, self._provider))
        wards_page = WardsPage(data, self._provider)
        self._pages = [overview_page, matches_page, heroes_page, wards_page]
        for page in self._pages:
            self._stack.addWidget(page)

        self._set_nav_enabled(True)
        self._select_page(min(self._current_page, len(self._pages) - 1))
        self._nav_account.setText(f"Steam32 · {data.account_id}")
        self.setWindowTitle(f"{APP_TITLE} — {data.profile.name}")

    def _remove_pages(self) -> None:
        for page in self._pages:
            shutdown = getattr(page, "shutdown", None)
            if callable(shutdown):
                shutdown()
            self._stack.removeWidget(page)
            page.deleteLater()
        self._pages.clear()

    def _select_page(self, index: int) -> None:
        if not self._pages or not 0 <= index < len(self._pages):
            return
        self._current_page = index
        self._stack.setCurrentWidget(self._pages[index])
        button = self._nav_buttons[index]
        if not button.isChecked():
            button.setChecked(True)

    def _set_nav_enabled(self, enabled: bool) -> None:
        for button in self._nav_buttons:
            button.setEnabled(enabled)

    def _set_status(self, text: str, kind: str) -> None:
        self._status_label.setText(text)
        object_name = {
            "ok": "AccentDot",
            "warn": "WarningDot",
            "error": "DangerDot",
        }.get(kind, "WarningDot")
        self._status_dot.setObjectName(object_name)
        self._status_dot.style().unpolish(self._status_dot)
        self._status_dot.style().polish(self._status_dot)
        self._status_dot.update()

    # ------------------------------------------------------------------
    # Settings / lifecycle
    # ------------------------------------------------------------------
    def open_settings(self) -> None:
        if self._closing:
            return
        dialog = SettingsDialog(self._config, self)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return
        new_config = dialog.result_config()
        old_config = self._config
        self._config = new_config
        self._store.save(new_config)

        if new_config.accent != old_config.accent:
            app = QApplication.instance()
            if app is not None:
                apply_theme(app, new_config.accent)

        account_changed = new_config.account_id != old_config.account_id
        if account_changed:
            self._data = None
            self._current_page = 0
            self._nav_buttons[0].setChecked(True)
            self._remove_pages()
            self._set_nav_enabled(False)
            self._stack.setCurrentWidget(self._loading_page)
            self._nav_account.setText(f"Steam32 · {new_config.account_id}")
            self.setWindowTitle(APP_TITLE)
            self.refresh_data(force=True)
        elif new_config.accent != old_config.accent:
            self._toast.show_message("Оформление обновлено.")
        else:
            self._toast.show_message("Настройки сохранены.")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._closing = True
        self._store.save_geometry(self.saveGeometry())
        self._loader.shutdown()
        for page in self._pages:
            shutdown = getattr(page, "shutdown", None)
            if callable(shutdown):
                shutdown()
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_toast") and self._toast.isVisible():
            self._position_toast()

    def _position_toast(self) -> None:
        if not hasattr(self, "_toast"):
            return
        self._toast.adjustSize()
        width = min(max(self._toast.sizeHint().width(), 280), 560)
        self._toast.setFixedWidth(width)
        self._toast.adjustSize()
        x = (self._central.width() - self._toast.width()) // 2
        y = self._central.height() - self._toast.height() - 54
        self._toast.move(max(16, x), max(16, y))

    def _set_initial_geometry(self) -> None:
        geometry = self._store.restore_geometry()
        if not geometry.isEmpty():
            self.restoreGeometry(geometry)
            screen = QApplication.primaryScreen()
            if screen is not None and screen.availableGeometry().intersects(self.geometry()):
                return

        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1200, 780)
            return
        available = screen.availableGeometry()
        width = min(1240, max(1024, available.width() - 120))
        height = min(820, max(640, available.height() - 100))
        self.resize(width, height)
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())
