from __future__ import annotations

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from data_tools import (
    DashboardData,
    format_duration,
    games_text,
)
from image_provider import ImageProvider
from theme import current_theme
from widgets import (
    EmptyState,
    FormStrip,
    HeroCard,
    HeroCell,
    HeroStatRow,
    MiniHeroRow,
    RemoteImage,
    ResultCell,
    StatCard,
    WinrateRing,
    make_badge,
)


def _title_block(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    layout.addWidget(title_label)
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("PageSubtitle")
    subtitle_label.setWordWrap(True)
    layout.addWidget(subtitle_label)
    return wrapper, layout


def scroll_page(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


class OverviewPage(QWidget):
    heroes_requested = Signal()
    matches_requested = Signal()

    def __init__(
        self,
        data: DashboardData,
        provider: ImageProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._data = data
        self._provider = provider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 26)
        layout.setSpacing(14)

        layout.addWidget(self._build_profile_card(data))
        layout.addLayout(self._build_stats(data))
        layout.addLayout(self._build_bottom(data), 1)

        footer_hint = QLabel("Данные профиля обновляются из OpenDota по запросу.")
        footer_hint.setObjectName("Dim")
        layout.addWidget(footer_hint)

    def _build_profile_card(self, data: DashboardData) -> QWidget:
        card = HeroCard()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        avatar = RemoteImage(self._provider, size=92, radius=46, circle=True, ring=True)
        avatar.setSource(data.profile.avatar_url, data.profile.name[:2])
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(4)
        caption = QLabel("ПРОФИЛЬ ИГРОКА")
        caption.setObjectName("ProfileCaption")
        info.addWidget(caption)

        name = QLabel(data.profile.name)
        name.setObjectName("ProfileName")
        name.setToolTip(data.profile.name)
        name.setMaximumWidth(580)
        info.addWidget(name)

        self._id_label = QLabel(f"Steam32 · {data.account_id}")
        self._id_label.setObjectName("ProfileMeta")
        info.addWidget(self._id_label)
        info.addSpacing(9)

        pills = QHBoxLayout()
        pills.setSpacing(7)
        pills.addWidget(make_badge(data.profile.rank_label, "rank"))
        if data.profile.country_code:
            pills.addWidget(make_badge(data.profile.country_code, "meta"))
        if data.profile.mmr_estimate:
            pills.addWidget(make_badge(f"MMR ≈ {data.profile.mmr_estimate}", "meta"))
        pills.addStretch(1)
        info.addLayout(pills)
        layout.addLayout(info, 1)

        ring = WinrateRing()
        ring.set_value(data.winrate)
        layout.addWidget(ring, 0, Qt.AlignmentFlag.AlignVCenter)
        return card

    def _build_stats(self, data: DashboardData) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)

        if data.matches:
            wins_hint = f"{data.wins} побед · {data.losses} поражений"
        else:
            wins_hint = "История матчей пуста"
        row.addWidget(
            StatCard(
                "Последние 20",
                f"{data.wins}–{data.losses}",
                wins_hint,
            ),
            1,
        )
        row.addWidget(
            StatCard(
                "Средний KDA",
                f"{data.avg_kda:.2f}",
                "K + A / D за последние матчи",
            ),
            1,
        )
        row.addWidget(
            StatCard(
                "Убийств за матч",
                f"{data.avg_kills:.1f}" if data.matches else "—",
                f"Смертей {data.avg_deaths:.1f} · ассистов {data.avg_assists:.1f}"
                if data.matches
                else "Нет данных",
            ),
            1,
        )
        row.addWidget(
            StatCard(
                "Средняя игра",
                format_duration(data.avg_duration) if data.avg_duration else "—",
                "Длительность матча",
            ),
            1,
        )
        return row

    def _build_bottom(self, data: DashboardData) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self._build_top_heroes(data), 11)
        row.addWidget(self._build_form(data), 9)
        return row

    def _build_top_heroes(self, data: DashboardData) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(0)

        header = QHBoxLayout()
        title = QLabel("Топ героев")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        all_button = QPushButton("Все герои →")
        all_button.setObjectName("Subtle")
        all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        all_button.clicked.connect(self.heroes_requested)
        header.addWidget(all_button)
        layout.addLayout(header)
        layout.addSpacing(2)
        subtitle = QLabel("По количеству матчей за всё время")
        subtitle.setObjectName("Dim")
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        if data.heroes:
            for index, hero in enumerate(data.heroes[:3]):
                layout.addWidget(MiniHeroRow(self._provider, hero, index))
                if index < min(3, len(data.heroes)) - 1:
                    layout.addSpacing(7)
        else:
            layout.addWidget(
                EmptyState(
                    "Герои не найдены",
                    "OpenDota не вернула статистику по героям.",
                ),
                1,
            )
        layout.addStretch(1)
        return card

    def _build_form(self, data: DashboardData) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(0)

        header = QHBoxLayout()
        title = QLabel("Форма")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        pill = QLabel("последние 10")
        pill.setObjectName("LivePill")
        header.addWidget(pill)
        layout.addLayout(header)
        layout.addSpacing(12)

        if data.form:
            form_wins = sum(1 for item in data.form if item)
            form_losses = len(data.form) - form_wins
            form_rate = form_wins / len(data.form) * 100
            value_row = QHBoxLayout()
            value_row.setSpacing(8)
            value = QLabel(f"{form_wins}–{form_losses}")
            value.setObjectName("StatValueSmall")
            value_row.addWidget(value)
            value_hint = QLabel("побед / поражений")
            value_hint.setObjectName("Muted")
            value_hint.setAlignment(Qt.AlignmentFlag.AlignBottom)
            value_row.addWidget(value_hint)
            value_row.addStretch(1)
            rate = QLabel(f"{form_rate:.0f}%")
            rate.setObjectName("WinRateHigh" if form_rate >= 50 else "WinRateLow")
            value_row.addWidget(rate)
            layout.addLayout(value_row)
            layout.addSpacing(8)

            strip = FormStrip()
            strip.set_matches(data.matches[:10][::-1])
            layout.addWidget(strip)

            layout.addSpacing(9)
            divider = QFrame()
            divider.setObjectName("Divider")
            layout.addWidget(divider)
            layout.addSpacing(9)

            legend = QHBoxLayout()
            legend.setSpacing(6)
            win_dot = QLabel()
            win_dot.setObjectName("AccentDot")
            win_dot.setFixedSize(7, 7)
            legend.addWidget(win_dot)
            win_label = QLabel("победа")
            win_label.setObjectName("Dim")
            legend.addWidget(win_label)
            legend.addSpacing(10)
            loss_dot = QLabel()
            loss_dot.setObjectName("DangerDot")
            loss_dot.setFixedSize(7, 7)
            legend.addWidget(loss_dot)
            loss_label = QLabel("поражение")
            loss_label.setObjectName("Dim")
            legend.addWidget(loss_label)
            legend.addStretch(1)
            layout.addLayout(legend)
        else:
            layout.addWidget(
                EmptyState(
                    "Нет матчей",
                    "История игр скрыта или ещё не загружена.",
                ),
                1,
            )
        layout.addStretch(1)
        return card


class MatchesPage(QWidget):
    def __init__(
        self,
        data: DashboardData,
        provider: ImageProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._data = data
        self._provider = provider
        self._row_matches = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 26)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(14)
        title_widget, _ = _title_block(
            "История матчей",
            f"Последние {len(data.matches)} игр · данные OpenDota",
        )
        header.addWidget(title_widget)
        header.addStretch(1)
        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        self._filters: list[QPushButton] = []
        for key, text, selected in (
            ("all", f"Все · {len(data.matches)}", True),
            ("win", f"Победы · {data.wins}", False),
            ("loss", f"Поражения · {data.losses}", False),
        ):
            button = QPushButton(text)
            button.setObjectName("Chip")
            button.setCheckable(True)
            button.setChecked(selected)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, value=key: self._apply_filter(value))
            self._filter_group.addButton(button)
            self._filters.append(button)
            header.addWidget(button)
        layout.addLayout(header)
        layout.addSpacing(2)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(9, 8, 9, 10)
        card_layout.setSpacing(0)

        if data.matches:
            self._table = QTableWidget()
            self._configure_table(data)
            card_layout.addWidget(self._table, 1)
            card_layout.addSpacing(8)
            footer = QHBoxLayout()
            hint = QLabel("Двойной клик по строке откроет матч на OpenDota")
            hint.setObjectName("Dim")
            footer.addWidget(hint)
            footer.addStretch(1)
            self._shown = QLabel(f"Показано {len(data.matches)} из {len(data.matches)}")
            self._shown.setObjectName("Dim")
            footer.addWidget(self._shown)
            card_layout.addLayout(footer)
        else:
            card_layout.addWidget(
                EmptyState(
                    "Матчи не найдены",
                    "OpenDota не вернула историю матчей. Проверьте настройки приватности.",
                ),
                1,
            )
            for button in self._filters:
                button.setEnabled(False)
        layout.addWidget(card, 1)

    def _configure_table(self, data: DashboardData) -> None:
        table = self._table
        headers = [
            "ГЕРОЙ",
            "РЕЗУЛЬТАТ",
            "K / D / A",
            "KDA",
            "ДЛИТЕЛЬНОСТЬ",
            "ДАТА",
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(data.matches))
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setWordWrap(False)
        table.setFrameShape(QFrame.Shape.NoFrame)
        table.verticalHeader().setDefaultSectionSize(50)

        header = table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        widths = {1: 118, 2: 102, 3: 68, 4: 108, 5: 99}
        for column, width in widths.items():
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(column, width)
        header.setStretchLastSection(False)

        theme = current_theme()
        number_font = QFont("Bahnschrift", 9)
        muted_font = QFont("Segoe UI", 9)
        for row, match in enumerate(data.matches):
            self._row_matches[row] = match
            table.setCellWidget(row, 0, HeroCell(self._provider, match))
            table.setCellWidget(row, 1, ResultCell(match.win))

            kda_item = QTableWidgetItem(match.kda_text)
            kda_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            kda_item.setFont(number_font)
            table.setItem(row, 2, kda_item)

            kda_value = QTableWidgetItem(f"{match.kda:.2f}")
            kda_value.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            kda_value.setFont(number_font)
            kda_value.setForeground(QColor(theme.text))
            table.setItem(row, 3, kda_value)

            duration = QTableWidgetItem(format_duration(match.duration))
            duration.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            duration.setFont(number_font)
            duration.setForeground(QColor(theme.text_muted))
            table.setItem(row, 4, duration)

            date = QTableWidgetItem(match.date_text)
            date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date.setFont(muted_font)
            date.setForeground(QColor(theme.text_muted))
            table.setItem(row, 5, date)

            side = "Radiant" if match.is_radiant else "Dire"
            tooltip = (
                f"Матч {match.match_id} · {side} · {match.hero_name}\n"
                f"K/D/A {match.kda_text} · KDA {match.kda:.2f}"
            )
            for column in range(6):
                item = table.item(row, column)
                if item is not None:
                    item.setToolTip(tooltip)
            for column in (0, 1):
                widget = table.cellWidget(row, column)
                if widget is not None:
                    widget.setToolTip(tooltip)

        table.cellDoubleClicked.connect(self._open_match)
        table.setToolTip("Двойной клик — открыть матч на OpenDota")

    def _apply_filter(self, key: str) -> None:
        if not hasattr(self, "_table"):
            return
        shown = 0
        for row, match in self._row_matches.items():
            visible = key == "all" or (key == "win" and match.win) or (key == "loss" and not match.win)
            self._table.setRowHidden(row, not visible)
            if visible:
                shown += 1
        self._shown.setText(f"Показано {shown} из {len(self._row_matches)}")

    def _open_match(self, row: int, column: int) -> None:
        del column
        match = self._row_matches.get(row)
        if match and match.match_id:
            QDesktopServices.openUrl(QUrl(f"https://www.opendota.com/matches/{match.match_id}"))


class HeroesPage(QWidget):
    def __init__(
        self,
        data: DashboardData,
        provider: ImageProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._data = data
        self._provider = provider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 26)
        layout.setSpacing(14)

        title_widget, _ = _title_block(
            "Статистика героев",
            "За всё время · топ по количеству матчей",
        )
        layout.addWidget(title_widget)

        summary = QHBoxLayout()
        summary.setSpacing(14)
        summary.addWidget(
            StatCard(
                "Всего героев",
                str(len(data.heroes)) if data.heroes else "—",
                "В истории игрока",
            ),
            1,
        )
        favorite = data.favorite_hero
        summary.addWidget(
            StatCard(
                "Любимый герой",
                favorite.name if favorite else "—",
                games_text(favorite.games) if favorite else "Нет данных",
                small_value=True,
            ),
            1,
        )
        summary.addWidget(
            StatCard(
                "Винрейт за всё время",
                f"{data.hero_overall_winrate:.1f}%"
                if data.total_hero_games
                else "—",
                f"{data.total_hero_wins} побед из {data.total_hero_games}"
                if data.total_hero_games
                else "Нет данных",
            ),
            1,
        )
        layout.addLayout(summary)

        list_card = QFrame()
        list_card.setObjectName("Card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(18, 16, 18, 18)
        list_layout.setSpacing(0)

        header = QHBoxLayout()
        title = QLabel("Топ-10 героев")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        caption = QLabel("ВИНРЕЙТ")
        caption.setObjectName("CardLabel")
        header.addWidget(caption)
        list_layout.addLayout(header)
        list_layout.addSpacing(2)
        subtitle = QLabel("По количеству сыгранных матчей")
        subtitle.setObjectName("Dim")
        list_layout.addWidget(subtitle)
        list_layout.addSpacing(12)

        if data.heroes:
            for index, hero in enumerate(data.heroes[:10]):
                list_layout.addWidget(HeroStatRow(self._provider, hero, index))
                if index < min(10, len(data.heroes)) - 1:
                    list_layout.addSpacing(7)
            if len(data.heroes) > 10:
                list_layout.addSpacing(10)
                more = QLabel(f"Показаны 10 из {len(data.heroes)} героев")
                more.setObjectName("Dim")
                list_layout.addWidget(more)
        else:
            list_layout.addWidget(
                EmptyState(
                    "Нет статистики героев",
                    "OpenDota не вернула данные по героям.",
                )
            )
        layout.addWidget(list_card)
        layout.addStretch(1)


def page_header(title: str, subtitle: str) -> tuple[QWidget, QLabel, QLabel]:
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("PageSubtitle")
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    return wrapper, title_label, subtitle_label
