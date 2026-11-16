from __future__ import annotations

import hashlib

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from data_tools import HeroItem, MatchItem, format_date, games_text, hero_icon_url
from image_provider import ImageProvider
from theme import THEMES, blend, current_theme, rgba


def display_font(size: int, weight: int = QFont.Weight.DemiBold) -> QFont:
    font = QFont("Bahnschrift", size)
    font.setWeight(weight)
    return font


def make_badge(text: str, kind: str = "meta") -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if kind == "win":
        label.setObjectName("WinBadge")
    elif kind == "loss":
        label.setObjectName("LossBadge")
    elif kind == "rank":
        label.setObjectName("RankPill")
    else:
        label.setObjectName("MetaPill")
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return label


class LogoMark(QWidget):
    def __init__(self, size: int = 40, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bounds = QRectF(1, 1, self.width() - 2, self.height() - 2)
        path = QPainterPath()
        path.addRoundedRect(bounds, self.width() * 0.27, self.width() * 0.27)

        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        gradient.setColorAt(0.0, QColor(theme.accent_light))
        gradient.setColorAt(1.0, QColor(theme.accent_dark))
        painter.fillPath(path, gradient)

        painter.save()
        painter.setClipPath(path)
        glow = QRadialGradient(
            bounds.left() + bounds.width() * 0.25,
            bounds.top() + bounds.height() * 0.18,
            bounds.width() * 0.9,
        )
        glow.setColorAt(0.0, QColor(255, 255, 255, 48))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(bounds, glow)
        painter.restore()

        font = QFont("Bahnschrift", max(8, int(self.width() * 0.31)))
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.2)
        painter.setFont(font)
        painter.setPen(QColor("#07130E"))
        painter.drawText(bounds, Qt.AlignmentFlag.AlignCenter, "D2")


class BrandPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(blend(theme.accent_deep, theme.bg, 0.18)))
        gradient.setColorAt(0.52, QColor(blend(theme.accent_deep, theme.bg, 0.58)))
        gradient.setColorAt(1.0, QColor(theme.bg))
        painter.fillRect(rect, gradient)

        glow = QRadialGradient(
            rect.width() * 0.76,
            rect.height() * 0.16,
            rect.width() * 0.9,
        )
        glow.setColorAt(0.0, QColor(theme.accent))
        glow.setColorAt(0.3, QColor(theme.accent))
        glow.setColorAt(1.0, QColor(theme.accent))
        accent = QColor(theme.accent)
        glow.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 42))
        glow.setColorAt(0.4, QColor(accent.red(), accent.green(), accent.blue(), 12))
        glow.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.fillRect(rect, glow)

        painter.setPen(QPen(QColor(255, 255, 255, 9), 1))
        step = 34
        for x in range(-rect.height(), rect.width() + rect.height(), step):
            painter.drawLine(x, 0, x + rect.height(), rect.height())
        for y in range(0, rect.height(), step):
            painter.drawLine(0, y, rect.width(), y)

        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 26), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            QRectF(rect.width() * 0.46, rect.height() * 0.54, rect.width() * 1.1, rect.width() * 1.1)
        )
        painter.drawEllipse(
            QRectF(rect.width() * 0.62, rect.height() * 0.66, rect.width() * 0.8, rect.width() * 0.8)
        )

        font = QFont("Bahnschrift", 170)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255, 7), 1))
        painter.drawText(
            QRectF(-30, rect.height() - 195, rect.width() + 120, 230),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            "02",
        )


class Spinner(QWidget):
    def __init__(self, size: int = 38, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(28)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(size, size)

    def _advance(self) -> None:
        self._angle = (self._angle + 9) % 360
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 5.0
        rect = QRectF(margin, margin, self.width() - margin * 2, self.height() - margin * 2)

        painter.setPen(QPen(QColor(theme.border_strong), 3.2))
        painter.drawArc(rect, 0, 360 * 16)

        pen = QPen(QColor(theme.accent), 3.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, (-self._angle + 90) * 16, -110 * 16)


class NavButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("NavButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        hint: str,
        small_value: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(0)

        top = QHBoxLayout()
        top.setSpacing(8)
        dot = QLabel()
        dot.setObjectName("AccentDot")
        dot.setFixedSize(6, 6)
        top.addWidget(dot)
        self._title = QLabel(title.upper())
        self._title.setObjectName("CardLabel")
        top.addWidget(self._title)
        top.addStretch(1)
        layout.addLayout(top)
        layout.addSpacing(9)

        self._value = QLabel(value)
        self._value.setObjectName("StatValueSmall" if small_value else "StatValue")
        if small_value:
            self._value.setWordWrap(False)
        layout.addWidget(self._value)
        layout.addSpacing(2)

        self._hint = QLabel(hint)
        self._hint.setObjectName("StatHint")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

    def set_value(self, value: str, hint: str | None = None) -> None:
        self._value.setText(value)
        if hint is not None:
            self._hint.setText(hint)


class WinrateRing(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self._display = 0.0
        self._has_data = False
        self._animation = QPropertyAnimation(self, b"displayValue", self)
        self._animation.setDuration(750)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMinimumSize(136, 136)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(152, 152)

    def get_display_value(self) -> float:
        return self._display

    def set_display_value(self, value: float) -> None:
        self._display = value
        self.update()

    displayValue = Property(float, get_display_value, set_display_value)

    def set_value(self, value: float, animate: bool = True) -> None:
        self._has_data = value > 0
        self._value = max(0.0, min(100.0, value))
        self._animation.stop()
        if animate:
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(self._value)
            self._animation.start()
        else:
            self.set_display_value(self._value)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = min(self.width(), self.height())
        margin = 10.0
        rect = QRectF(
            (self.width() - width) / 2 + margin,
            (self.height() - width) / 2 + margin,
            width - margin * 2,
            width - margin * 2,
        )

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(theme.surface_high), 9.2))
        painter.drawArc(rect, 0, 360 * 16)

        color = QColor(theme.accent if self._value >= 45 or not self._has_data else theme.danger)
        if self._has_data:
            glow_pen = QPen(QColor(color.red(), color.green(), color.blue(), 46), 18)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(rect, 90 * 16, int(-self._display / 100 * 360 * 16))

            pen = QPen(color, 9.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, int(-self._display / 100 * 360 * 16))

        painter.setPen(QColor(theme.text))
        value_font = QFont("Bahnschrift", 27)
        value_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(value_font)
        value = f"{round(self._display)}%" if self._has_data else "—"
        painter.drawText(
            QRectF(rect.left(), rect.top() - 2, rect.width(), rect.height() * 0.62),
            Qt.AlignmentFlag.AlignCenter,
            value,
        )

        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor(theme.text_dim))
        caption = "ВИНРЕЙТ" if self._has_data else "НЕТ МАТЧЕЙ"
        painter.drawText(
            QRectF(rect.left(), rect.top() + rect.height() * 0.58, rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            caption,
        )


class HeroCard(QFrame):
    """Панель профиля с собственной градиентной отрисовкой."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(0.8, 0.8, self.width() - 1.6, self.height() - 1.6)
        path = QPainterPath()
        path.addRoundedRect(bounds, 16, 16)

        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        gradient.setColorAt(0.0, QColor(blend(theme.accent_deep, theme.surface, 0.55)))
        gradient.setColorAt(0.5, QColor(theme.surface))
        gradient.setColorAt(1.0, QColor(theme.bg_alt))
        painter.fillPath(path, gradient)

        painter.save()
        painter.setClipPath(path)
        glow = QRadialGradient(
            bounds.right() - 170,
            bounds.top() + 60,
            310,
        )
        accent = QColor(theme.accent)
        glow.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 36))
        glow.setColorAt(0.55, QColor(accent.red(), accent.green(), accent.blue(), 8))
        glow.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.fillRect(bounds, glow)

        painter.setPen(QPen(QColor(255, 255, 255, 8), 1))
        for offset in (0, 46, 92):
            painter.drawLine(
                int(bounds.right() - 80 - offset),
                int(bounds.top()),
                int(bounds.right() - 210 - offset),
                int(bounds.bottom()),
            )
        painter.restore()

        painter.setPen(QPen(QColor(theme.border), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


class FormStrip(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._matches: list[MatchItem] = []
        self.setMinimumHeight(44)
        self.setMouseTracking(True)

    def set_matches(self, matches: list[MatchItem]) -> None:
        self._matches = matches
        self.update()

    def _block_rect(self, index: int, count: int) -> QRectF:
        available = self.width() - 4
        gap = 5.0
        block_width = (available - gap * max(0, count - 1)) / max(1, count)
        return QRectF(2 + index * (block_width + gap), 7, block_width, 30)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        count = max(1, len(self._matches))
        for index in range(count):
            rect = self._block_rect(index, count)
            if index >= len(self._matches):
                painter.setBrush(QColor(theme.surface_high))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect, 5, 5)
                continue
            match = self._matches[index]
            base = QColor(theme.accent if match.win else theme.danger)
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            bright = QColor(base)
            bright.setAlpha(235)
            dark = QColor(base)
            dark.setAlpha(135)
            gradient.setColorAt(0.0, bright)
            gradient.setColorAt(1.0, dark)
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 5, 5)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._matches:
            count = len(self._matches)
            for index in range(count):
                if self._block_rect(index, count).adjusted(-2, -5, 2, 5).contains(event.position()):
                    match = self._matches[index]
                    result = "Победа" if match.win else "Поражение"
                    self.setToolTip(f"{result} · {match.hero_name} · {format_date(match.start_time)}")
                    return
        self.setToolTip("")
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setToolTip("")
        super().leaveEvent(event)


class RemoteImage(QWidget):
    def __init__(
        self,
        provider: ImageProvider,
        size: int = 40,
        radius: int = 10,
        circle: bool = False,
        ring: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._provider = provider
        self._url = ""
        self._pixmap: QPixmap | None = None
        self._fallback = "D2"
        self._radius = radius
        self._circle = circle
        self._ring = ring
        self._base_color = QColor("#294238")
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        provider.pixmap_ready.connect(self._on_pixmap_ready)

    def setSource(self, url: str, fallback: str = "D2") -> None:  # noqa: N802
        self._url = (url or "").strip()
        self._fallback = fallback or "D2"
        self._base_color = self._fallback_color(self._fallback or self._url)
        if self._url:
            pixmap = self._provider.get(self._url)
            if pixmap is not None:
                self._pixmap = pixmap
                self.update()
                return
        self._pixmap = None
        self.update()

    def _on_pixmap_ready(self, url: str, pixmap: QPixmap) -> None:
        if self._url and url == self._url:
            self._pixmap = pixmap
            self.update()

    @staticmethod
    def _fallback_color(key: str) -> QColor:
        palette = ("#2D5B4B", "#3B4D6B", "#5A3E54", "#5B4D2D", "#2D5566", "#493D66", "#4D3A35")
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return QColor(palette[int(digest[:8], 16) % len(palette)])

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        if self._circle:
            path.addEllipse(bounds)
        else:
            path.addRoundedRect(bounds, self._radius, self._radius)

        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        gradient.setColorAt(0.0, self._base_color.lighter(118))
        gradient.setColorAt(1.0, self._base_color.darker(145))
        painter.fillPath(path, gradient)

        if self._pixmap is not None:
            painter.save()
            painter.setClipPath(path)
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(-x, -y, scaled)
            painter.restore()
        else:
            font = QFont("Bahnschrift", max(8, int(self.width() * 0.27)))
            font.setWeight(QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("#EFFAF5"))
            painter.drawText(bounds, Qt.AlignmentFlag.AlignCenter, self._fallback[:2].upper())

        if self._ring:
            accent = QColor(theme.accent)
            painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 200), 2))
        else:
            painter.setPen(QPen(QColor(theme.border_strong), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


class HeroCell(QWidget):
    def __init__(
        self,
        provider: ImageProvider,
        match: MatchItem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 0, 0)
        layout.setSpacing(10)
        icon = RemoteImage(provider, size=30, radius=8)
        icon.setSource(hero_icon_url(match.hero_slug), match.hero_name[:2])
        layout.addWidget(icon)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        name = QLabel(match.hero_name)
        name.setObjectName("HeroName")
        text_layout.addWidget(name)
        side = QLabel("Radiant" if match.is_radiant else "Dire")
        side.setObjectName("HeroMeta")
        text_layout.addWidget(side)
        layout.addLayout(text_layout)
        layout.addStretch(1)


class ResultCell(QWidget):
    def __init__(self, win: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 0, 3, 0)
        badge = QLabel("ПОБЕДА" if win else "ПОРАЖЕНИЕ")
        badge.setObjectName("WinBadge" if win else "LossBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedHeight(24)
        layout.addWidget(badge)
        layout.addStretch(1)


class HeroStatRow(QFrame):
    def __init__(
        self,
        provider: ImageProvider,
        hero: HeroItem,
        index: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SoftCard")
        self.setFixedHeight(72)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 9, 16, 9)
        layout.setSpacing(12)

        rank = QLabel(f"{index + 1:02d}")
        rank.setObjectName("RankNumberTop" if index < 3 else "RankNumber")
        rank.setFixedWidth(24)
        rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(rank)

        icon = RemoteImage(provider, size=42, radius=10)
        icon.setSource(hero_icon_url(hero.slug), hero.name[:2])
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        name = QLabel(hero.name)
        name.setObjectName("HeroName")
        text_layout.addWidget(name)
        meta = QLabel(f"{games_text(hero.games)} · {hero.wins} побед")
        meta.setObjectName("HeroMeta")
        text_layout.addWidget(meta)
        layout.addLayout(text_layout, 1)

        rate_label = QLabel(f"{hero.winrate:.0f}%")
        rate_label.setObjectName("WinRateHigh" if hero.winrate >= 50 else "WinRateLow")
        rate_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        rate_label.setFixedWidth(58)
        layout.addWidget(rate_label)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(round(hero.winrate))
        progress.setTextVisible(False)
        progress.setFixedWidth(150)
        if hero.winrate < 50:
            progress.setObjectName("DangerBar")
        layout.addWidget(progress)

        self.setToolTip(
            f"{hero.name}: {games_text(hero.games)}, побед {hero.wins}, "
            f"поражений {hero.losses}, винрейт {hero.winrate:.1f}%"
        )


class MiniHeroRow(QFrame):
    def __init__(
        self,
        provider: ImageProvider,
        hero: HeroItem,
        index: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SoftCard")
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 7, 12, 7)
        layout.setSpacing(10)

        rank = QLabel(f"{index + 1}")
        rank.setObjectName("RankNumberTop" if index == 0 else "RankNumber")
        rank.setFixedWidth(16)
        rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(rank)

        icon = RemoteImage(provider, size=34, radius=8)
        icon.setSource(hero_icon_url(hero.slug), hero.name[:2])
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        name = QLabel(hero.name)
        name.setObjectName("HeroName")
        text_layout.addWidget(name)
        meta = QLabel(games_text(hero.games))
        meta.setObjectName("HeroMeta")
        text_layout.addWidget(meta)
        layout.addLayout(text_layout, 1)

        rate = QLabel(f"{hero.winrate:.0f}%")
        rate.setObjectName("WinRateHigh" if hero.winrate >= 50 else "WinRateLow")
        layout.addWidget(rate)


class EmptyState(QWidget):
    def __init__(
        self,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 34, 26, 34)
        layout.setSpacing(8)
        layout.addStretch(1)
        glyph = QLabel("—")
        glyph.setObjectName("Accent")
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glyph.setFont(display_font(26))
        layout.addWidget(glyph)
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        text = QLabel(description)
        text.setObjectName("Muted")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch(1)


class LoadingPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)
        layout.addStretch(1)

        logo = LogoMark(56)
        logo_row = QHBoxLayout()
        logo_row.addStretch(1)
        logo_row.addWidget(logo)
        logo_row.addStretch(1)
        layout.addLayout(logo_row)
        layout.addSpacing(26)

        spinner = Spinner(42)
        spinner_row = QHBoxLayout()
        spinner_row.addStretch(1)
        spinner_row.addWidget(spinner)
        spinner_row.addStretch(1)
        layout.addLayout(spinner_row)
        layout.addSpacing(18)

        title = QLabel("Подключаемся к OpenDota")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(7)

        self._status = QLabel("Загружаем профиль игрока")
        self._status.setObjectName("Muted")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)
        layout.addStretch(1)

    def set_status(self, text: str) -> None:
        self._status.setText(text)


class ErrorPage(QWidget):
    retry_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)
        layout.addStretch(1)

        icon = QFrame()
        icon.setObjectName("ErrorIcon")
        icon.setFixedSize(76, 76)
        icon_layout = QVBoxLayout(icon)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        glyph = QLabel("!")
        glyph.setObjectName("ErrorGlyph")
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(glyph)
        icon_row = QHBoxLayout()
        icon_row.addStretch(1)
        icon_row.addWidget(icon)
        icon_row.addStretch(1)
        layout.addLayout(icon_row)
        layout.addSpacing(20)

        title = QLabel("Не удалось загрузить профиль")
        title.setObjectName("ErrorTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(8)

        self._message = QLabel()
        self._message.setObjectName("ErrorText")
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)
        self._message.setMaximumWidth(560)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self._message)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addSpacing(22)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        retry = QPushButton("Повторить")
        retry.setObjectName("Primary")
        retry.setCursor(Qt.CursorShape.PointingHandCursor)
        retry.clicked.connect(self.retry_requested)
        buttons.addWidget(retry)
        settings = QPushButton("Настройки")
        settings.setObjectName("Ghost")
        settings.setCursor(Qt.CursorShape.PointingHandCursor)
        settings.clicked.connect(self.settings_requested)
        buttons.addWidget(settings)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)

    def set_error(self, message: str) -> None:
        self._message.setText(message)


class AccentPicker(QWidget):
    accent_changed = Signal(str)

    def __init__(self, selected: str = "emerald", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected = selected
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for key, theme in THEMES.items():
            button = QPushButton(theme.name)
            button.setObjectName("Chip")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(self._make_dot(theme.accent))
            button.setIconSize(QSize(13, 13))
            if key == selected:
                button.setChecked(True)
            button.clicked.connect(lambda _checked=False, accent_key=key: self._choose(accent_key))
            self._group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)
        layout.addStretch(1)

    @staticmethod
    def _make_dot(color: str) -> QIcon:
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawEllipse(3, 3, 10, 10)
        painter.end()
        return QIcon(pixmap)

    def _choose(self, key: str) -> None:
        if key == self._selected:
            return
        self._selected = key
        self.accent_changed.emit(key)

    def selected(self) -> str:
        return self._selected

    def set_selected(self, key: str) -> None:
        if key not in self._buttons:
            return
        self._selected = key
        self._buttons[key].setChecked(True)


class Toast(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 16, 10)
        layout.setSpacing(10)
        dot = QLabel()
        dot.setObjectName("AccentDot")
        dot.setFixedSize(6, 6)
        layout.addWidget(dot)
        self._label = QLabel()
        self._label.setObjectName("Muted")
        self._label.setWordWrap(True)
        layout.addWidget(self._label)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_message(self, text: str, duration: int = 3800) -> None:
        self._label.setText(text)
        self.adjustSize()
        self.setFixedWidth(min(max(self.sizeHint().width(), 260), 520))
        self.adjustSize()
        self.show()
        self.raise_()
        self._timer.start(duration)
