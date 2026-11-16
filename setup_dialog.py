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
from paths import APP_VERSION
from theme import apply_theme
from widgets import AccentPicker, BrandPanel, LogoMark


def _feature(number: str, title: str, text: str) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(13)

    index = QLabel(number)
    index.setObjectName("SetupEyebrow")
    index.setFixedWidth(22)
    index.setAlignment(Qt.AlignmentFlag.AlignTop)
    layout.addWidget(index)

    text_layout = QVBoxLayout()
    text_layout.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("BrandFeatureTitle")
    text_layout.addWidget(title_label)
    text_label = QLabel(text)
    text_label.setObjectName("BrandFeatureText")
    text_label.setWordWrap(True)
    text_layout.addWidget(text_label)
    layout.addLayout(text_layout, 1)
    return widget


def _set_invalid(field: QLineEdit, invalid: bool) -> None:
    field.setProperty("invalid", "true" if invalid else "false")
    field.style().unpolish(field)
    field.style().polish(field)
    field.update()


class SetupDialog(QDialog):
    def __init__(
        self,
        initial: AppConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = initial or AppConfig()
        self.setObjectName("SetupDialog")
        self.setWindowTitle("Dota 2 Pulse — первичная настройка")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(960, 620)
        self.setMinimumSize(900, 590)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_brand(), 0)

        right = QWidget()
        right.setObjectName("SetupRight")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(54, 38, 54, 34)
        right_layout.setSpacing(0)
        root.addWidget(right, 1)

        top = QHBoxLayout()
        eyebrow = QLabel("ПЕРВИЧНАЯ НАСТРОЙКА")
        eyebrow.setObjectName("SetupEyebrow")
        top.addWidget(eyebrow)
        top.addStretch(1)
        api_pill = QLabel("OpenDota API")
        api_pill.setObjectName("LivePill")
        top.addWidget(api_pill)
        right_layout.addLayout(top)
        right_layout.addSpacing(38)

        title = QLabel("Подключи свой аккаунт")
        title.setObjectName("SetupTitle")
        title.setWordWrap(True)
        right_layout.addWidget(title)
        right_layout.addSpacing(8)
        lead = QLabel(
            "Один раз укажи Steam ID — приложение запомнит аккаунт "
            "и будет открывать аналитику при следующем запуске."
        )
        lead.setObjectName("SetupLead")
        lead.setWordWrap(True)
        lead.setMaximumWidth(520)
        right_layout.addWidget(lead)
        right_layout.addSpacing(30)

        field_label = QLabel("STEAM ID ИЛИ ССЫЛКА НА ПРОФИЛЬ")
        field_label.setObjectName("FieldLabel")
        right_layout.addWidget(field_label)
        right_layout.addSpacing(7)

        self._field = QLineEdit()
        self._field.setPlaceholderText("Например, 86745912")
        self._field.setClearButtonEnabled(True)
        self._field.setText(str(self._config.account_id) if self._config.account_id else "")
        self._field.textChanged.connect(self._clear_error)
        self._field.returnPressed.connect(self._start)
        right_layout.addWidget(self._field)
        right_layout.addSpacing(7)

        hint = QLabel(
            "Steam32 ID, Steam64 ID или ссылка на профиль OpenDota / Dotabuff / Stratz."
        )
        hint.setObjectName("FieldHint")
        hint.setWordWrap(True)
        right_layout.addWidget(hint)
        right_layout.addSpacing(6)

        self._error = QLabel("")
        self._error.setObjectName("FieldError")
        self._error.setWordWrap(True)
        self._error.setMinimumHeight(18)
        right_layout.addWidget(self._error)
        right_layout.addSpacing(17)

        accent_label = QLabel("АКЦЕНТ ИНТЕРФЕЙСА")
        accent_label.setObjectName("FieldLabel")
        right_layout.addWidget(accent_label)
        right_layout.addSpacing(8)
        self._accents = AccentPicker(self._config.accent)
        self._accents.accent_changed.connect(self._preview_accent)
        right_layout.addWidget(self._accents)
        right_layout.addSpacing(5)
        accent_hint = QLabel("Можно изменить позже в настройках.")
        accent_hint.setObjectName("FieldHint")
        right_layout.addWidget(accent_hint)
        right_layout.addStretch(1)

        divider = QFrame()
        divider.setObjectName("Divider")
        right_layout.addWidget(divider)
        right_layout.addSpacing(20)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        note = QLabel("Настройки хранятся только локально")
        note.setObjectName("FieldHint")
        note.setWordWrap(True)
        note.setMaximumWidth(250)
        buttons.addWidget(note)
        buttons.addStretch(1)
        cancel = QPushButton("Выход")
        cancel.setObjectName("Ghost")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self._start_button = QPushButton("Загрузить профиль")
        self._start_button.setObjectName("Primary")
        self._start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_button.setDefault(True)
        self._start_button.clicked.connect(self._start)
        buttons.addWidget(self._start_button)
        right_layout.addLayout(buttons)

    def _build_brand(self) -> QWidget:
        panel = BrandPanel()
        panel.setFixedWidth(390)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 36, 38, 30)
        layout.setSpacing(0)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(13)
        logo_row.addWidget(LogoMark(44))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_title = QLabel("DOTA 2 PULSE")
        brand_title.setObjectName("AppTitle")
        brand_text.addWidget(brand_title)
        brand_subtitle = QLabel("PROFILE INTELLIGENCE")
        brand_subtitle.setObjectName("AppSubtitle")
        brand_text.addWidget(brand_subtitle)
        logo_row.addLayout(brand_text)
        logo_row.addStretch(1)
        layout.addLayout(logo_row)
        layout.addStretch(1)

        title = QLabel("Каждый матч\nимеет значение.")
        title.setObjectName("BrandTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        layout.addSpacing(12)
        subtitle = QLabel("Профиль, форма и любимые герои —\nв одном спокойном интерфейсе.")
        subtitle.setObjectName("BrandSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(36)

        layout.addWidget(
            _feature(
                "01",
                "Профиль и ранг",
                "Аватар, текущий ранг и оценка MMR.",
            )
        )
        layout.addSpacing(18)
        layout.addWidget(
            _feature(
                "02",
                "Последние 20 матчей",
                "Результат, K/D/A, GPM и длительность.",
            )
        )
        layout.addSpacing(18)
        layout.addWidget(
            _feature(
                "03",
                "Статистика героев",
                "Топ героев, количество игр и винрейт.",
            )
        )
        layout.addStretch(1)

        footer = QHBoxLayout()
        footer_text = QLabel("Данные: OpenDota API")
        footer_text.setObjectName("BrandFooter")
        footer.addWidget(footer_text)
        footer.addStretch(1)
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("BrandFooter")
        footer.addWidget(version)
        layout.addLayout(footer)
        return panel

    def _preview_accent(self, key: str) -> None:
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, key)

    def _clear_error(self) -> None:
        if self._error.text():
            self._error.setText("")
            _set_invalid(self._field, False)

    def _start(self) -> None:
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
