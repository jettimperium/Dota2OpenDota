from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from config import AppConfig, ConfigStore
from main_window import MainWindow
from paths import APP_NAME, APP_TITLE, APP_VERSION, log_dir, resource_path
from setup_dialog import SetupDialog
from theme import apply_theme


def _configure_logging() -> Path:
    log_path = log_dir() / "dota2pulse.log"
    handler = RotatingFileHandler(
        log_path,
        maxBytes=500_000,
        backupCount=2,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    return log_path


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dota2Pulse.Desktop.1")
    except Exception:  # noqa: BLE001 — необязательный cosmetic-вызов
        pass


def _load_app_icon(app: QApplication) -> None:
    icon_path = resource_path("assets/app.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))


def _install_exception_hook(log_path: Path) -> None:
    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.getLogger("dota2pulse").critical("Необработанная ошибка:\n%s", details)
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("Dota 2 Pulse — ошибка")
        box.setText("Приложение столкнулось с неожиданной ошибкой.")
        box.setInformativeText(
            f"{exc_value}\n\nПодробности записаны в:\n{log_path}"
        )
        box.exec()

    sys.excepthook = handle_exception


def main() -> int:
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationDisplayName(APP_TITLE)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    _set_windows_app_id()
    log_path = _configure_logging()
    _install_exception_hook(log_path)
    _load_app_icon(app)
    logging.getLogger("dota2pulse").info("Запуск %s v%s", APP_TITLE, APP_VERSION)

    store = ConfigStore()
    config = store.load()
    apply_theme(app, config.accent)

    if "--smoke-test" in sys.argv:
        smoke = QWidget()
        smoke.setWindowTitle("Dota 2 Pulse — smoke test")
        smoke.resize(420, 220)
        smoke.show()
        QTimer.singleShot(500, app.quit)
        return app.exec()

    should_setup = config.account_id is None or "--setup" in sys.argv
    if should_setup:
        dialog = SetupDialog(config)
        accepted = dialog.exec() == SetupDialog.DialogCode.Accepted
        if accepted:
            config = dialog.result_config()
            store.save(config)
            apply_theme(app, config.accent)
            logging.getLogger("dota2pulse").info("Настроен аккаунт Steam32 %s", config.account_id)
        elif config.account_id is None:
            return 0
        else:
            apply_theme(app, config.accent)

    window = MainWindow(config, store)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
