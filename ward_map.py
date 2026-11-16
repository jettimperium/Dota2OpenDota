from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from data_tools import WardPlacement, entity_display_name, format_match_time
from dota_map import DotaMapRenderer, MapProjection
from theme import current_theme

OBSERVER_COLOR = "#FFD54A"
SENTRY_COLOR = "#4FB3FF"


class WardMap(QWidget):
    """Интерактивная карта Dota 2 7.41 с журналом вардов OpenDota."""

    hover_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._wards: list[WardPlacement] = []
        self._duration = 0
        self._time_filter: int | None = None
        self._show_observer = True
        self._show_sentry = True
        self._hovered: WardPlacement | None = None
        self._selected: WardPlacement | None = None
        self._loaded = False
        self._empty_text = "Нет данных"
        self._projection_cache: MapProjection | None = None
        self._projection_rect = QRectF()
        self._renderer = DotaMapRenderer()
        self.setMouseTracking(True)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip(
            "Точная карта Dota 2 7.41: вышки, лесные лагеря, река и Рошан. "
            "Наведите на вард, чтобы увидеть подробности."
        )

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(560, 560)

    def set_data(
        self,
        wards: list[WardPlacement],
        duration: int,
        loaded: bool = True,
        empty_text: str = "",
    ) -> None:
        self._wards = list(wards or [])
        self._duration = max(0, int(duration or 0))
        self._loaded = loaded
        self._empty_text = empty_text or "В этом матче нет вардов"
        self._hovered = None
        self._selected = None
        self.setToolTip("")
        self.update()

    def set_time_filter(self, seconds: int | None) -> None:
        self._time_filter = seconds
        self.update()

    def set_selected(self, ward: WardPlacement | None) -> None:
        self._selected = ward
        self.update()

    def set_kind_visible(self, kind: str, visible: bool) -> None:
        if kind == "observer":
            self._show_observer = visible
        elif kind == "sentry":
            self._show_sentry = visible
        self.update()

    def visible_wards(self) -> list[WardPlacement]:
        result: list[WardPlacement] = []
        for ward in self._wards:
            if ward.is_observer and not self._show_observer:
                continue
            if not ward.is_observer and not self._show_sentry:
                continue
            if self._time_filter is not None and not ward.is_active_at(self._time_filter):
                continue
            result.append(ward)
        return result

    # ------------------------------------------------------------------
    # Geometry / painting
    # ------------------------------------------------------------------
    def _map_rect(self) -> QRectF:
        side = min(self.width(), self.height()) - 12
        if side < 40:
            return QRectF()
        return QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2,
            side,
            side,
        )

    def _projection(self, rect: QRectF) -> MapProjection:
        if self._projection_cache is None or self._projection_rect != rect:
            self._projection_cache = MapProjection(rect)
            self._projection_rect = QRectF(rect)
        return self._projection_cache

    def _point_in(self, rect: QRectF, x: float, y: float) -> QPointF:
        return self._projection(rect).ground(x, y)

    def _marker_lift(self, rect: QRectF) -> float:
        return max(1.5, rect.width() * 0.007)

    def _marker_point(self, rect: QRectF, ward: WardPlacement) -> QPointF:
        point = self._point_in(rect, ward.x, ward.y)
        return QPointF(point.x(), point.y() - self._marker_lift(rect))

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        theme = current_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._map_rect()
        if rect.width() < 40:
            return

        canvas_path = QPainterPath()
        canvas_path.addRoundedRect(rect, 14, 14)
        painter.fillPath(canvas_path, QColor(theme.bg_alt))

        painter.save()
        painter.setClipPath(canvas_path)
        self._renderer.paint(painter, rect, theme)
        self._paint_wards(painter, rect)
        painter.restore()

        painter.setPen(QPen(QColor(theme.border_strong), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(canvas_path)

        if self._loaded and not self.visible_wards():
            text = (
                "Нет активных вардов в этот момент"
                if self._time_filter is not None
                else self._empty_text
            )
            painter.setFont(self.font())
            painter.setPen(QColor(theme.text_dim))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _paint_wards(self, painter: QPainter, rect: QRectF) -> None:
        visible = self.visible_wards()
        for ward in visible:
            base = self._point_in(rect, ward.x, ward.y)
            marker = self._marker_point(rect, ward)
            radius = max(4.4, rect.width() * 0.0135)
            opacity = 1.0
            if self._time_filter is None and ward.ended_at <= self._duration:
                opacity = 0.56
            if ward is self._hovered:
                opacity = 1.0
                radius *= 1.13
            self._paint_ward_marker(painter, base, marker, radius, ward, opacity)

        if self._selected is not None and self._selected in visible:
            marker = self._marker_point(rect, self._selected)
            radius = max(4.4, rect.width() * 0.0135) * 1.95
            pen = QPen(QColor(255, 255, 255, 205), max(1.0, rect.width() * 0.004))
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(marker, radius, radius)

    def _paint_ward_marker(
        self,
        painter: QPainter,
        base: QPointF,
        point: QPointF,
        radius: float,
        ward: WardPlacement,
        opacity: float,
    ) -> None:
        base_color = QColor(OBSERVER_COLOR if ward.is_observer else SENTRY_COLOR)
        painter.save()
        painter.setOpacity(opacity)

        # Anchor glow and shadow stay on the terrain surface.
        glow = QRadialGradient(base, radius * 3.2)
        glow.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 70))
        glow.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(base, radius * 3.0, radius * 1.55)

        painter.setBrush(QColor(0, 0, 0, 92))
        painter.drawEllipse(
            QPointF(base.x() + radius * 0.35, base.y() + radius * 0.45),
            radius * 0.95,
            radius * 0.40,
        )
        painter.setBrush(QColor(base_color.red(), base_color.green(), base_color.blue(), 110))
        painter.drawEllipse(base, radius * 0.78, radius * 0.33)

        # A short mast lifts the ward above the terrain.
        stem_pen = QPen(
            QColor(base_color.red(), base_color.green(), base_color.blue(), 190),
            max(0.9, radius * 0.20),
        )
        stem_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(stem_pen)
        painter.drawLine(base, QPointF(point.x(), point.y() + radius * 0.45))

        glow = QRadialGradient(point, radius * 3.3)
        glow.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 100))
        glow.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(point, radius * 3.3, radius * 3.3)

        outline = QPen(QColor("#071017"), max(1.0, radius * 0.24))
        outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(outline)
        if ward.is_observer:
            painter.setBrush(base_color)
            painter.drawEllipse(point, radius, radius)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#EAF8FF"))
            painter.drawEllipse(point, radius * 0.54, radius * 0.34)
            painter.setBrush(QColor("#071017"))
            painter.drawEllipse(point, radius * 0.18, radius * 0.18)
        else:
            path = QPainterPath()
            path.moveTo(point.x(), point.y() - radius * 1.12)
            path.lineTo(point.x() + radius * 1.08, point.y())
            path.lineTo(point.x(), point.y() + radius * 1.12)
            path.lineTo(point.x() - radius * 1.08, point.y())
            path.closeSubpath()
            painter.setBrush(base_color)
            painter.drawPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#FFF7E8"))
            painter.drawEllipse(point, radius * 0.30, radius * 0.30)

        if ward is self._hovered:
            painter.setOpacity(1.0)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 210), max(1.3, radius * 0.22)))
            painter.drawEllipse(point, radius * 1.8, radius * 1.8)
        painter.restore()

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------
    def _ward_at(self, position: QPointF) -> WardPlacement | None:
        rect = self._map_rect()
        if rect.width() < 40:
            return None
        threshold = max(9.0, rect.width() * 0.027)
        best: WardPlacement | None = None
        best_distance = threshold * threshold
        for ward in self.visible_wards():
            point = self._marker_point(rect, ward)
            distance = (point.x() - position.x()) ** 2 + (point.y() - position.y()) ** 2
            if distance <= best_distance:
                best = ward
                best_distance = distance
        return best

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        ward = self._ward_at(event.position())
        if ward is not self._hovered:
            self._hovered = ward
            self.hover_changed.emit(ward)
            self.update()
        if ward is not None:
            self.setToolTip(self._tooltip_for(ward))
        else:
            rect = self._map_rect()
            feature = self._renderer.feature_at(rect, event.position())
            self.setToolTip(feature)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if self._hovered is not None:
            self._hovered = None
            self.hover_changed.emit(None)
            self.update()
        self.setToolTip("")
        super().leaveEvent(event)

    def _tooltip_for(self, ward: WardPlacement) -> str:
        lines = [
            f"{ward.kind_title} Ward",
            f"Установлен: {format_match_time(ward.placed_at)}",
        ]
        if ward.removed_at is not None:
            lines.append(f"Снят: {format_match_time(ward.removed_at)}")
            if ward.attackername:
                lines.append(f"Кем: {entity_display_name(ward.attackername)}")
        elif ward.expires_at <= self._duration:
            lines.append(f"Истёк: {format_match_time(ward.expires_at)}")
        else:
            lines.append("Действует до конца матча")
        lines.append(f"Координаты: {ward.x:.0f}, {ward.y:.0f}")
        return "\n".join(lines)
