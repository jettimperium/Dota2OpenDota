from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from data_tools import (
    DashboardData,
    MatchItem,
    MatchWards,
    WardPlacement,
    entity_display_name,
    format_duration,
    format_match_time,
    hero_icon_url,
)
from image_provider import ImageProvider
from service import MatchWardsLoader
from ward_map import OBSERVER_COLOR, SENTRY_COLOR, WardMap
from widgets import EmptyState, RemoteImage, Spinner, make_badge


def _dot_icon(color: str, size: int = 13) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.end()
    return QIcon(pixmap)


def _title_block(title: str, subtitle: str) -> QWidget:
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    layout.addWidget(title_label)
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("PageSubtitle")
    layout.addWidget(subtitle_label)
    return wrapper


class WardMatchRow(QWidget):
    """Строка выбора матча: иконка героя, результат и дата."""

    def __init__(
        self,
        provider: ImageProvider,
        match: MatchItem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(9)

        icon = RemoteImage(provider, size=34, radius=8)
        icon.setSource(hero_icon_url(match.hero_slug), match.hero_name[:2])
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        name = QLabel(match.hero_name)
        name.setObjectName("HeroName")
        text_layout.addWidget(name)
        meta = QLabel(f"{match.date_text} · {format_duration(match.duration)}")
        meta.setObjectName("HeroMeta")
        text_layout.addWidget(meta)
        layout.addLayout(text_layout, 1)

        result = QLabel("ПОБЕДА" if match.win else "ПОРАЖЕНИЕ")
        result.setObjectName("WinBadge" if match.win else "LossBadge")
        result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result.setFixedHeight(20)
        result.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(result)


class WardListRow(QWidget):
    """Компактная строка установки в правой колонке."""

    def __init__(
        self,
        ward: WardPlacement,
        status: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 4, 7, 4)
        layout.setSpacing(8)

        dot = QLabel()
        dot.setPixmap(
            _dot_icon(OBSERVER_COLOR if ward.is_observer else SENTRY_COLOR).pixmap(12, 12)
        )
        dot.setFixedSize(12, 12)
        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        title = QLabel(f"{format_match_time(ward.placed_at)} · {ward.kind_title}")
        title.setObjectName("HeroName")
        text_layout.addWidget(title)
        subtitle = QLabel(status)
        subtitle.setObjectName("HeroMeta")
        text_layout.addWidget(subtitle)
        layout.addLayout(text_layout, 1)


class WardsPage(QWidget):
    """Страница выбора матча и карты вардов игрока."""

    def __init__(
        self,
        data: DashboardData,
        provider: ImageProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._data = data
        self._provider = provider
        self._matches = list(data.matches)
        self._selected_match: MatchItem | None = None
        self._wards: MatchWards | None = None
        self._request_id = 0
        self._loader = MatchWardsLoader(self)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.failed.connect(self._on_failed)
        self._loader.parse_requested.connect(self._on_parse_requested)

        self._build_ui()
        if self._matches:
            self._match_list.setCurrentRow(0)
        else:
            self._show_no_matches()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(
            _title_block(
                "Карта вардов",
                "Варды игрока на точной карте 7.41: вышки, лесные лагеря и река",
            )
        )
        header.addStretch(1)
        layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(self._build_match_panel(), 0)
        content.addWidget(self._build_map_panel(), 1)
        content.addWidget(self._build_ward_panel(), 0)
        layout.addLayout(content, 1)

    def _build_match_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(300)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(13, 13, 13, 13)
        layout.setSpacing(6)

        caption = QLabel("МАТЧИ")
        caption.setObjectName("CardLabel")
        layout.addWidget(caption)
        subtitle = QLabel("Выберите игру")
        subtitle.setObjectName("Dim")
        layout.addWidget(subtitle)

        self._match_list = QListWidget()
        self._match_list.setObjectName("WardMatchList")
        self._match_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._match_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._match_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._match_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._match_list.setSpacing(0)
        for match in self._matches:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 58))
            item.setToolTip(
                f"{match.hero_name} · {'Победа' if match.win else 'Поражение'}\n"
                f"{match.date_text} · {format_duration(match.duration)} · "
                f"K/D/A {match.kda_text}"
            )
            self._match_list.addItem(item)
            self._match_list.setItemWidget(item, WardMatchRow(self._provider, match))
        self._match_list.currentRowChanged.connect(self._on_match_row_changed)
        layout.addWidget(self._match_list, 1)

        if not self._matches:
            layout.removeWidget(self._match_list)
            self._match_list.hide()
            layout.addWidget(
                EmptyState(
                    "Матчи не найдены",
                    "OpenDota не вернула историю матчей для этого профиля.",
                ),
                1,
            )

        hint = QLabel(
            "Журнал вардов появляется только у матчей, которые OpenDota уже разобрала."
        )
        hint.setObjectName("Dim")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return card

    def _build_map_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(10)
        self._hero_icon = RemoteImage(self._provider, size=44, radius=10)
        header.addWidget(self._hero_icon, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        self._match_title = QLabel("—")
        self._match_title.setObjectName("SectionTitle")
        text_layout.addWidget(self._match_title)
        self._match_meta = QLabel("Выберите матч")
        self._match_meta.setObjectName("Dim")
        text_layout.addWidget(self._match_meta)
        header.addLayout(text_layout, 1)

        self._parse_badge = make_badge("—", "meta")
        header.addWidget(self._parse_badge, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self._map_stack = QStackedWidget()
        self._map_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self._map = WardMap()
        self._map.hover_changed.connect(self._on_ward_hovered)
        self._map_stack.addWidget(self._map)
        self._loading_panel = self._build_loading_panel()
        self._map_stack.addWidget(self._loading_panel)
        self._message_panel = self._build_message_panel()
        self._map_stack.addWidget(self._message_panel)
        self._map_stack.setCurrentWidget(self._loading_panel)
        layout.addWidget(self._map_stack, 1)

        self._terrain_legend = QLabel(
            "Точная карта 7.41 · 22 вышки · 28 лесных лагерей"
        )
        self._terrain_legend.setObjectName("Dim")
        self._terrain_legend.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._terrain_legend.setToolTip(
            "Зелёные и красные квадраты — вышки Radiant и Dire, светлые круги — "
            "обычные лагеря, коричневые спирали — древние. Жёлтые маркеры — "
            "Observer, синие — Sentry."
        )
        layout.addWidget(self._terrain_legend)

        time_row = QHBoxLayout()
        time_row.setSpacing(7)
        self._time_check = QCheckBox("Только активные")
        self._time_check.setObjectName("WardTimeCheck")
        self._time_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self._time_check.setToolTip(
            "Показать только те варды, которые были активны в выбранный момент матча"
        )
        self._time_check.toggled.connect(self._on_time_toggled)
        time_row.addWidget(self._time_check)
        self._time_slider = QSlider(Qt.Orientation.Horizontal)
        self._time_slider.setRange(0, 0)
        self._time_slider.setSingleStep(10)
        self._time_slider.setPageStep(60)
        self._time_slider.setEnabled(False)
        self._time_slider.valueChanged.connect(self._on_time_changed)
        time_row.addWidget(self._time_slider, 1)
        self._time_label = QLabel("весь матч")
        self._time_label.setObjectName("WardTime")
        self._time_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._time_label.setMinimumWidth(56)
        time_row.addWidget(self._time_label)
        layout.addLayout(time_row)

        footer = QHBoxLayout()
        footer.setSpacing(7)
        self._obs_chip = QPushButton("Observer · —")
        self._obs_chip.setObjectName("Chip")
        self._obs_chip.setCheckable(True)
        self._obs_chip.setChecked(True)
        self._obs_chip.setIcon(_dot_icon(OBSERVER_COLOR))
        self._obs_chip.setIconSize(QSize(12, 12))
        self._obs_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        self._obs_chip.toggled.connect(
            lambda checked: self._map.set_kind_visible("observer", checked)
        )
        footer.addWidget(self._obs_chip)

        self._sen_chip = QPushButton("Sentry · —")
        self._sen_chip.setObjectName("Chip")
        self._sen_chip.setCheckable(True)
        self._sen_chip.setChecked(True)
        self._sen_chip.setIcon(_dot_icon(SENTRY_COLOR))
        self._sen_chip.setIconSize(QSize(12, 12))
        self._sen_chip.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sen_chip.toggled.connect(
            lambda checked: self._map.set_kind_visible("sentry", checked)
        )
        footer.addWidget(self._sen_chip)

        self._ward_hint = QLabel("Наведите на маркер")
        self._ward_hint.setObjectName("Dim")
        self._ward_hint.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._ward_hint.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        footer.addWidget(self._ward_hint, 1)
        layout.addLayout(footer)
        return card

    def _build_loading_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addStretch(1)
        spinner = Spinner(36)
        spinner_row = QHBoxLayout()
        spinner_row.addStretch(1)
        spinner_row.addWidget(spinner)
        spinner_row.addStretch(1)
        layout.addLayout(spinner_row)
        label = QLabel("Загружаем подробности матча")
        label.setObjectName("Muted")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch(1)
        return panel

    def _build_message_panel(self) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        box = QFrame()
        box.setObjectName("SoftCard")
        box.setMaximumWidth(560)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(22, 18, 22, 18)
        box_layout.setSpacing(8)

        self._msg_title = QLabel("Загрузка")
        self._msg_title.setObjectName("SectionTitle")
        self._msg_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(self._msg_title)

        self._msg_text = QLabel()
        self._msg_text.setObjectName("Muted")
        self._msg_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_text.setWordWrap(True)
        box_layout.addWidget(self._msg_text)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(8)
        buttons.setVerticalSpacing(6)
        self._retry_button = QPushButton("Проверить снова")
        self._retry_button.setObjectName("Primary")
        self._retry_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._retry_button.clicked.connect(self._reload_selected)
        buttons.addWidget(self._retry_button, 0, 0)

        self._parse_button = QPushButton("Запросить парсинг")
        self._parse_button.setObjectName("Ghost")
        self._parse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._parse_button.clicked.connect(self._request_parse)
        buttons.addWidget(self._parse_button, 0, 1)

        self._open_button = QPushButton("Открыть на OpenDota")
        self._open_button.setObjectName("Subtle")
        self._open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_button.clicked.connect(self._open_selected)
        buttons.addWidget(self._open_button, 1, 0, 1, 2)
        box_layout.addLayout(buttons)

        outer.addWidget(box, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)
        return panel

    def _build_ward_panel(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(268)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(13, 13, 13, 13)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("Установки")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self._ward_count = QLabel("0")
        self._ward_count.setObjectName("LivePill")
        header.addWidget(self._ward_count)
        layout.addLayout(header)

        subtitle = QLabel("По времени матча")
        subtitle.setObjectName("Dim")
        layout.addWidget(subtitle)

        self._ward_empty = QLabel("Выберите матч")
        self._ward_empty.setObjectName("Dim")
        self._ward_empty.setWordWrap(True)
        self._ward_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._ward_empty, 1)

        self._ward_list = QListWidget()
        self._ward_list.setObjectName("WardList")
        self._ward_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._ward_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._ward_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._ward_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._ward_list.itemSelectionChanged.connect(self._on_ward_selected)
        self._ward_list.hide()
        layout.addWidget(self._ward_list, 1)

        self._ward_summary = QLabel("Наблюдатели 0 · Сентри 0")
        self._ward_summary.setObjectName("Dim")
        self._ward_summary.setWordWrap(True)
        layout.addWidget(self._ward_summary)

        hint = QLabel("Выберите установку, чтобы подсветить её на карте.")
        hint.setObjectName("Dim")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return card

    # ------------------------------------------------------------------
    # Match selection / loading
    # ------------------------------------------------------------------
    def _on_match_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._matches):
            self._select_match(self._matches[row])

    def _select_match(self, match: MatchItem) -> None:
        self._selected_match = match
        self._wards = None
        self._request_id = 0
        self._parse_button.setVisible(False)
        self._parse_button.setEnabled(True)
        self._parse_button.setText("Запросить парсинг")
        self._set_badge("ЗАГРУЗКА", "meta")
        self._update_match_header(match)
        self._clear_ward_panel("Загружаем варды…")
        self._map.set_data([], 0, loaded=False)
        self._map_stack.setCurrentWidget(self._loading_panel)
        self._obs_chip.setText("Observer · —")
        self._sen_chip.setText("Sentry · —")
        self._obs_chip.setEnabled(False)
        self._sen_chip.setEnabled(False)
        self._time_check.setChecked(False)
        self._time_check.setEnabled(False)
        self._time_slider.setRange(0, 0)
        self._time_slider.setEnabled(False)
        self._time_label.setText("весь матч")
        self._ward_hint.setText("Загружаем матч…")
        self._request_id = self._loader.start(self._data.account_id, match.match_id)

    def _update_match_header(self, match: MatchItem) -> None:
        self._hero_icon.setSource(hero_icon_url(match.hero_slug), match.hero_name[:2])
        self._match_title.setText(match.hero_name)
        side = "Radiant" if match.is_radiant else "Dire"
        result = "Победа" if match.win else "Поражение"
        self._match_meta.setText(
            f"{result} · {match.date_text} · {format_duration(match.duration)}"
        )
        self._match_meta.setToolTip(
            f"{side} · K/D/A {match.kda_text} · матч {match.match_id}"
        )

    def _on_loaded(self, request_id: int, payload) -> None:
        if request_id != self._request_id or not isinstance(payload, MatchWards):
            return
        match = self._selected_match
        if match is None or payload.match_id != match.match_id:
            return
        self._wards = payload

        self._obs_chip.setText(f"Observer · {payload.observer_count}")
        self._sen_chip.setText(f"Sentry · {payload.sentry_count}")
        self._obs_chip.setEnabled(True)
        self._sen_chip.setEnabled(True)
        self._obs_chip.setChecked(True)
        self._sen_chip.setChecked(True)

        self._map.set_data(
            payload.wards,
            payload.duration,
            loaded=True,
            empty_text="В этом матче игрок не ставил варды",
        )
        self._time_slider.setRange(0, max(0, payload.duration))
        self._time_slider.setValue(max(0, payload.duration // 2))
        self._time_check.setChecked(False)
        self._time_check.setEnabled(payload.duration > 0 and payload.total > 0)
        self._time_slider.setEnabled(False)
        self._time_label.setText("весь матч")

        if not payload.player_found:
            self._set_badge("НЕТ ИГРОКА", "loss")
            self._clear_ward_panel("Игрок не найден в этом матче.")
            self._show_message(
                "Игрок не найден",
                "В карточке матча нет игрока с текущим Steam32 ID.",
                parse_visible=False,
            )
            self._ward_hint.setText("Игрок не найден")
            return

        if not payload.parsed:
            self._set_badge("НЕ РАЗОБРАН", "meta")
            self._clear_ward_panel("Данные появятся после парсинга.")
            self._show_message(
                "Матч ещё не разобран",
                "OpenDota не хранит журнал вардов для этого матча. Можно запросить "
                "парсинг — он выполняется на стороне OpenDota и обычно занимает "
                "несколько минут. После этого нажмите «Проверить снова».",
                parse_visible=True,
            )
            self._ward_hint.setText("Нужен парсинг матча")
            return

        self._set_badge("РАЗОБРАН", "win")
        self._map_stack.setCurrentWidget(self._map)
        self._populate_ward_panel(payload)
        if payload.total:
            self._ward_hint.setText("Наведите на маркер")
        else:
            self._ward_hint.setText("В этом матче нет вардов игрока")

    def _on_failed(self, request_id: int, message: str) -> None:
        if request_id != self._request_id:
            return
        self._set_badge("ОШИБКА", "loss")
        self._clear_ward_panel("Не удалось загрузить данные.")
        self._show_message(
            "Не удалось загрузить матч",
            message,
            parse_visible=False,
        )
        self._ward_hint.setText("Ошибка загрузки")

    def _show_message(self, title: str, text: str, parse_visible: bool) -> None:
        self._msg_title.setText(title)
        self._msg_text.setText(text)
        self._parse_button.setVisible(parse_visible)
        self._parse_button.setEnabled(parse_visible)
        self._parse_button.setText("Запросить парсинг")
        self._retry_button.setVisible(True)
        self._open_button.setVisible(True)
        self._map_stack.setCurrentWidget(self._message_panel)
        self._time_check.setEnabled(False)
        self._time_slider.setRange(0, 0)
        self._time_slider.setValue(0)
        self._time_slider.setEnabled(False)
        self._time_label.setText("—")
        self._obs_chip.setEnabled(False)
        self._sen_chip.setEnabled(False)

    def _show_no_matches(self) -> None:
        self._match_title.setText("Нет матчей")
        self._match_meta.setText("История матчей пуста")
        self._set_badge("—", "meta")
        self._clear_ward_panel("Нет матчей для отображения.")
        self._show_message(
            "Нет матчей",
            "OpenDota не вернула историю матчей. Проверьте настройки приватности "
            "или обновите данные профиля.",
            parse_visible=False,
        )
        self._obs_chip.setEnabled(False)
        self._sen_chip.setEnabled(False)
        self._ward_hint.setText("Нет данных")

    def _reload_selected(self) -> None:
        if self._selected_match is not None:
            self._select_match(self._selected_match)

    # ------------------------------------------------------------------
    # Ward panel
    # ------------------------------------------------------------------
    def _clear_ward_panel(self, text: str) -> None:
        self._ward_list.clear()
        self._ward_list.hide()
        self._ward_empty.setText(text)
        self._ward_empty.show()
        self._ward_count.setText("0")
        self._ward_summary.setText("Наблюдатели 0 · Сентри 0")

    def _populate_ward_panel(self, payload: MatchWards) -> None:
        self._ward_list.clear()
        self._ward_count.setText(str(payload.total))
        self._ward_summary.setText(
            f"Наблюдатели {payload.observer_count} · Сентри {payload.sentry_count}"
        )
        if not payload.wards:
            self._ward_list.hide()
            self._ward_empty.setText("В этом матче игрок не ставил варды.")
            self._ward_empty.show()
            return

        self._ward_empty.hide()
        self._ward_list.show()
        for index, ward in enumerate(payload.wards):
            status = self._ward_status(ward, payload.duration)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 44))
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setToolTip(self._ward_tooltip(ward, payload.duration))
            self._ward_list.addItem(item)
            self._ward_list.setItemWidget(item, WardListRow(ward, status))

    @staticmethod
    def _ward_status(ward: WardPlacement, duration: int) -> str:
        if ward.removed_at is not None:
            return f"снят {format_match_time(ward.removed_at)}"
        if ward.expires_at <= duration:
            return f"истёк {format_match_time(ward.expires_at)}"
        return "не снят до конца"

    @staticmethod
    def _ward_tooltip(ward: WardPlacement, duration: int) -> str:
        lines = [
            f"{ward.kind_title} Ward",
            f"Установлен: {format_match_time(ward.placed_at)}",
        ]
        if ward.removed_at is not None:
            lines.append(f"Снят: {format_match_time(ward.removed_at)}")
            if ward.attackername:
                lines.append(f"Кем: {entity_display_name(ward.attackername)}")
        elif ward.expires_at <= duration:
            lines.append(f"Истёк: {format_match_time(ward.expires_at)}")
        else:
            lines.append("Действует до конца матча")
        return "\n".join(lines)

    def _on_ward_selected(self) -> None:
        if self._wards is None:
            return
        items = self._ward_list.selectedItems()
        if not items:
            self._map.set_selected(None)
            return
        index = items[0].data(Qt.ItemDataRole.UserRole)
        if isinstance(index, int) and 0 <= index < self._wards.total:
            ward = self._wards.wards[index]
            if self._time_check.isChecked() and not ward.is_active_at(
                self._time_slider.value()
            ):
                target = max(0, min(ward.placed_at, self._time_slider.maximum()))
                self._time_slider.setValue(target)
            self._map.set_selected(ward)

    def _on_ward_hovered(self, ward: object) -> None:
        if not isinstance(ward, WardPlacement):
            self._ward_hint.setText("Наведите на маркер")
            return
        self._ward_hint.setText(
            f"{format_match_time(ward.placed_at)} · {ward.kind_title}"
        )

    # ------------------------------------------------------------------
    # Filters / actions
    # ------------------------------------------------------------------
    def _on_time_toggled(self, checked: bool) -> None:
        self._time_slider.setEnabled(checked and self._time_slider.maximum() > 0)
        if checked:
            value = self._time_slider.value()
            self._map.set_time_filter(value)
            self._time_label.setText(format_duration(value))
        else:
            self._map.set_time_filter(None)
            self._time_label.setText("весь матч")

    def _on_time_changed(self, value: int) -> None:
        if self._time_check.isChecked():
            self._map.set_time_filter(value)
            self._time_label.setText(format_duration(value))

    def _request_parse(self) -> None:
        if self._selected_match is None:
            return
        self._parse_button.setEnabled(False)
        self._parse_button.setText("Отправляем…")
        self._msg_text.setText(
            "Отправляем запрос в OpenDota. Это может занять несколько секунд."
        )
        self._loader.request_parse(self._selected_match.match_id)

    def _on_parse_requested(self, match_id: int, success: bool, message: str) -> None:
        if self._selected_match is None or match_id != self._selected_match.match_id:
            return
        if success:
            self._msg_title.setText("Запрос отправлен")
            self._msg_text.setText(
                "OpenDota поставила матч в очередь на парсинг. Обычно это занимает "
                "несколько минут. После завершения нажмите «Проверить снова»."
            )
            self._parse_button.setVisible(True)
            self._parse_button.setEnabled(False)
            self._parse_button.setText("Запрос отправлен")
        else:
            self._msg_text.setText(message)
            self._parse_button.setVisible(True)
            self._parse_button.setEnabled(True)
            self._parse_button.setText("Запросить парсинг")

    def _open_selected(self) -> None:
        if self._selected_match is not None:
            QDesktopServices.openUrl(
                QUrl(f"https://www.opendota.com/matches/{self._selected_match.match_id}")
            )

    def _set_badge(self, text: str, kind: str) -> None:
        object_name = {
            "win": "WinBadge",
            "loss": "LossBadge",
            "meta": "MetaPill",
        }.get(kind, "MetaPill")
        self._parse_badge.setText(text)
        self._parse_badge.setObjectName(object_name)
        self._parse_badge.style().unpolish(self._parse_badge)
        self._parse_badge.style().polish(self._parse_badge)
        self._parse_badge.updateGeometry()
        self._parse_badge.adjustSize()

    def shutdown(self) -> None:
        self._loader.shutdown()
