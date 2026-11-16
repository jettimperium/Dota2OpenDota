from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from accounts import AccountIdError, parse_account_id
from config import AppConfig
from theme import apply_theme
from widgets import AccentPicker, LogoMark


def _set_invalid(field: QLineEdit, invalid: bool) -> None:
    field.setProperty("invalid", "true" if invalid else "false")
    field.style().unpolish(field)
    field.style().polish(field)
    field.update()


class SettingsDialog(QDialog):
    def __init__(
        self,
        current: AppConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._original = current
        self._config = current
        self._preview_key = current.accent

        self.setObjectName("SettingsDialog")
        self.setWindowTitle("Dota 2 Pulse — настройки")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(640, 590)
        self.setMinimumWidth(610)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 30, 32, 28)
        root.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(LogoMark(38))
        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        eyebrow = QLabel("DOTA 2 PULSE")
        eyebrow.setObjectName("SetupEyebrow")
        title_block.addWidget(eyebrow)
        title = QLabel("Настройки")
        title.setObjectName("PageTitle")
        title_block.addWidget(title)
        header.addLayout(title_block)
        header.addStretch(1)
        root.addLayout(header)
        root.addSpacing(22)

        subtitle = QLabel("Аккаунт OpenDota и акцент интерфейса. Изменения применяются сразу.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        root.addSpacing(24)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(0)

        field_label = QLabel("STEAM ID ИЛИ ССЫЛКА НА ПРОФИЛЬ")
        field_label.setObjectName("FieldLabel")
        card_layout.addWidget(field_label)
        card_layout.addSpacing(7)
        self._field = QLineEdit()
        self._field.setPlaceholderText("Например, 86745912")
        self._field.setClearButtonEnabled(True)
        self._field.setText(str(current.account_id) if current.account_id else "")
        self._field.textChanged.connect(self._clear_error)
        self._field.returnPressed.connect(self._save)
        card_layout.addWidget(self._field)
        card_layout.addSpacing(6)
        hint = QLabel(
            "Можно вставить Steam32 ID, Steam64 ID или ссылку на OpenDota / Dotabuff / Stratz."
        )
        hint.setObjectName("FieldHint")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)
        card_layout.addSpacing(5)
        self._error = QLabel("")
        self._error.setObjectName("FieldError")
        self._error.setMinimumHeight(17)
        self._error.setWordWrap(True)
        card_layout.addWidget(self._error)
        card_layout.addSpacing(12)

        divider = QFrame()
        divider.setObjectName("Divider")
        card_layout.addWidget(divider)
        card_layout.addSpacing(16)

        accent_label = QLabel("АКЦЕНТ ИНТЕРФЕЙСА")
        accent_label.setObjectName("FieldLabel")
        card_layout.addWidget(accent_label)
        card_layout.addSpacing(8)
        self._accents = AccentPicker(current.accent)
        self._accents.accent_changed.connect(self._preview_accent)
        card_layout.addWidget(self._accents)
        card_layout.addSpacing(6)
        accent_hint = QLabel("Цвет кнопок, графиков и активных элементов.")
        accent_hint.setObjectName("FieldHint")
        card_layout.addWidget(accent_hint)
        root.addWidget(card)
        root.addStretch(1)

        note = QLabel("Аккаунт можно сменить в любой момент — профиль загрузится заново.")
        note.setObjectName("FieldHint")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addSpacing(16)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = QPushButton("Отмена")
        cancel.setObjectName("Ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Сохранить")
        save.setObjectName("Primary")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setDefault(True)
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _preview_accent(self, key: str) -> None:
        self._preview_key = key
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, key)

    def _clear_error(self) -> None:
        if self._error.text():
            self._error.setText("")
            _set_invalid(self._field, False)

    def _save(self) -> None:
        try:
            account_id = parse_account_id(self._field.text())
        except AccountIdError as error:
            self._error.setText(str(error))
            _set_invalid(self._field, True)
            self._field.setFocus()
            return
        self._config = AppConfig(account_id=account_id, accent=self._accents.selected())
        self.accept()

    def result_config(self) -> AppConfig:
        return self._config

    def reject(self) -> None:
        app = QApplication.instance()
        if app is not None and self._preview_key != self._original.accent:
            apply_theme(app, self._original.accent)
        super().reject()
