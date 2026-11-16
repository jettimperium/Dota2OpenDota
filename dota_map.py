from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
    QTransform,
)

from paths import resource_path

MAP_SIZE = 256.0
GRID_CELLS = 72
RIVER_HALF_WIDTH = 11.5
RADIANT_COLOR = "#55DFA4"
DIRE_COLOR = "#FF7279"


@dataclass(frozen=True, slots=True)
class Tower:
    x: float
    y: float
    team: str
    lane: str
    tier: int


@dataclass(frozen=True, slots=True)
class Camp:
    x: float
    y: float
    tier: str
    side: str


@dataclass(frozen=True, slots=True)
class Ramp:
    x: float
    y: float
    angle: float
    length: float = 13.5
    width: float = 7.2


@dataclass(frozen=True, slots=True)
class Bridge:
    x: float
    y: float
    angle: float
    length: float = 16.0
    width: float = 11.0


TOWERS: tuple[Tower, ...] = (
    # 7.41 map data: 11 towers per side, including two Tier 4 towers.
    Tower(55.1, 46.7, "dire", "top", 1),
    Tower(40.6, 105.5, "radiant", "top", 1),
    Tower(134.2, 122.4, "dire", "mid", 1),
    Tower(106.0, 151.4, "radiant", "mid", 1),
    Tower(212.6, 163.1, "dire", "bottom", 1),
    Tower(193.3, 221.2, "radiant", "bottom", 1),
    Tower(125.3, 47.0, "dire", "top", 2),
    Tower(161.1, 101.9, "dire", "mid", 2),
    Tower(214.3, 126.2, "dire", "bottom", 2),
    Tower(38.3, 143.8, "radiant", "top", 2),
    Tower(83.5, 172.7, "radiant", "mid", 2),
    Tower(122.1, 219.5, "radiant", "bottom", 2),
    Tower(175.5, 50.4, "dire", "top", 3),
    Tower(185.3, 78.7, "dire", "mid", 3),
    Tower(213.5, 89.0, "dire", "bottom", 3),
    Tower(37.1, 179.5, "radiant", "top", 3),
    Tower(63.7, 189.8, "radiant", "mid", 3),
    Tower(73.1, 217.5, "radiant", "bottom", 3),
    Tower(194.5, 64.4, "dire", "base", 4),
    Tower(199.1, 69.3, "dire", "base", 4),
    Tower(49.1, 200.0, "radiant", "base", 4),
    Tower(53.5, 204.6, "radiant", "base", 4),
)

CAMPS: tuple[Camp, ...] = (
    # 7.41 neutral camps: 6 small, 14 medium, 6 hard, 2 ancient.
    Camp(87.7, 27.9, "small", "dire"),
    Camp(242.0, 113.8, "small", "dire"),
    Camp(73.7, 63.7, "small", "dire"),
    Camp(181.3, 202.2, "small", "radiant"),
    Camp(164.8, 248.8, "small", "radiant"),
    Camp(17.6, 157.4, "small", "radiant"),
    Camp(154.5, 20.6, "medium", "dire"),
    Camp(131.6, 23.4, "medium", "dire"),
    Camp(91.6, 77.5, "medium", "dire"),
    Camp(69.6, 14.4, "medium", "dire"),
    Camp(143.7, 72.9, "medium", "dire"),
    Camp(115.4, 62.1, "medium", "dire"),
    Camp(173.3, 151.4, "medium", "dire"),
    Camp(117.2, 239.8, "medium", "radiant"),
    Camp(94.1, 249.7, "medium", "radiant"),
    Camp(153.2, 187.5, "medium", "radiant"),
    Camp(187.3, 250.1, "medium", "radiant"),
    Camp(129.6, 204.6, "medium", "radiant"),
    Camp(72.3, 117.6, "medium", "radiant"),
    Camp(100.0, 199.3, "medium", "radiant"),
    Camp(61.2, 76.5, "hard", "dire"),
    Camp(141.5, 95.3, "hard", "dire"),
    Camp(235.2, 133.3, "hard", "dire"),
    Camp(13.6, 139.4, "hard", "radiant"),
    Camp(190.5, 183.6, "hard", "radiant"),
    Camp(107.2, 178.8, "hard", "radiant"),
    Camp(186.4, 130.9, "ancient", "dire"),
    Camp(58.6, 132.9, "ancient", "radiant"),
)

RAMPS: tuple[Ramp, ...] = (
    Ramp(62, 160, -96),
    Ramp(83, 201, 12),
    Ramp(93, 169, 52),
    Ramp(196, 84, 96),
    Ramp(171, 56, 186),
    Ramp(165, 88, 226),
    Ramp(126, 143, -104),
    Ramp(187, 154, 165),
    Ramp(118, 135, 72),
    Ramp(60, 94, 18),
    Ramp(80, 110, -44),
    Ramp(178, 148, 136),
    Ramp(137, 58, 142),
    Ramp(105, 190, 8),
)

BRIDGES: tuple[Bridge, ...] = (
    Bridge(65, 96, 84, 17.0, 12.0),
    Bridge(128, 128, -42, 18.0, 11.0),
    Bridge(193, 162, 84, 17.0, 12.0),
)

RUNE_POINTS: tuple[tuple[float, float], ...] = ((104.6, 115.9), (143.1, 148.7))
ROSHAN_PITS: tuple[tuple[float, float], ...] = ((83.4, 97.9), (165.6, 170.1))
SHRINE_POINTS: tuple[tuple[float, float, str], ...] = (
    (25.3, 229.1, "radiant"),
    (228.1, 35.3, "dire"),
)

RIVER_POINTS: tuple[tuple[float, float], ...] = (
    (-12, 48),
    (25, 64),
    (63, 95),
    (91, 111),
    (128, 128),
    (164, 146),
    (193, 162),
    (225, 178),
    (268, 198),
)

TOP_LANE: tuple[tuple[float, float], ...] = (
    (74, 178),
    (70, 160),
    (65, 136),
    (64, 108),
    (68, 82),
    (84, 68),
    (108, 63),
    (142, 63),
    (168, 67),
    (181, 74),
)
MID_LANE: tuple[tuple[float, float], ...] = (
    (74, 178),
    (88, 168),
    (100, 157),
    (114, 143),
    (128, 128),
    (141, 113),
    (156, 98),
    (170, 84),
    (181, 76),
)
BOTTOM_LANE: tuple[tuple[float, float], ...] = (
    (74, 178),
    (92, 188),
    (120, 192),
    (148, 192),
    (172, 185),
    (187, 170),
    (193, 148),
    (194, 122),
    (192, 96),
    (187, 83),
)

LANES: tuple[tuple[tuple[float, float], ...], ...] = (TOP_LANE, MID_LANE, BOTTOM_LANE)

FOREST_CLUSTERS: tuple[tuple[float, float, float, float, int], ...] = (
    (142, 172, 48, 28, 62),
    (177, 145, 28, 22, 24),
    (146, 207, 42, 18, 28),
    (108, 82, 46, 25, 58),
    (77, 120, 27, 24, 24),
    (110, 51, 45, 17, 26),
    (43, 145, 23, 30, 17),
    (204, 119, 22, 27, 16),
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _ellipse_mask(
    x: float,
    y: float,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    inner: float = 0.64,
    outer: float = 0.98,
) -> float:
    distance = math.hypot((x - cx) / rx, (y - cy) / ry)
    return 1.0 - _smoothstep(inner, outer, distance)


def _point_segment_distance(
    x: float,
    y: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 0.0001:
        return math.hypot(x - x1, y - y1)
    t = _clamp(((x - x1) * dx + (y - y1) * dy) / length_sq)
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def _polyline_distance(x: float, y: float, points: tuple[tuple[float, float], ...]) -> float:
    return min(
        _point_segment_distance(x, y, *points[index], *points[index + 1])
        for index in range(len(points) - 1)
    )


def _river_distance(x: float, y: float) -> float:
    return _polyline_distance(x, y, RIVER_POINTS)


def terrain_height(x: float, y: float) -> float:
    """Procedural height of the Dota map, in the same 0..255 surface grid."""

    x = _clamp(x, 0.0, MAP_SIZE)
    y = _clamp(y, 0.0, MAP_SIZE)

    height = 0.145
    height += 0.105 * _ellipse_mask(x, y, 103, 88, 72, 58, 0.00, 1.28)
    height += 0.095 * _ellipse_mask(x, y, 153, 168, 72, 58, 0.00, 1.28)

    # Raised side shelves along the outer lanes.
    height = max(height, 0.265 + 0.265 * _ellipse_mask(x, y, 84, 143, 31, 37, 0.65, 0.97))
    height = max(height, 0.265 + 0.265 * _ellipse_mask(x, y, 172, 113, 31, 37, 0.65, 0.97))

    # Main jungle plateaus.
    height = max(height, 0.285 + 0.355 * _ellipse_mask(x, y, 150, 177, 53, 39, 0.70, 0.96))
    height = max(height, 0.285 + 0.355 * _ellipse_mask(x, y, 106, 79, 53, 39, 0.70, 0.96))

    # Small upper terraces inside both jungles.
    height = max(height, 0.355 + 0.190 * _ellipse_mask(x, y, 160, 190, 24, 18, 0.60, 0.92))
    height = max(height, 0.355 + 0.190 * _ellipse_mask(x, y, 96, 66, 24, 18, 0.60, 0.92))

    # Radiant and Dire base high ground.
    height = max(height, 0.400 + 0.510 * _ellipse_mask(x, y, 72, 184, 41, 35, 0.74, 0.96))
    height = max(height, 0.400 + 0.510 * _ellipse_mask(x, y, 184, 72, 41, 35, 0.74, 0.96))

    # Roshan pits sit in small depressions beside the river.
    pit = max(
        _ellipse_mask(x, y, 73, 103, 23, 18, 0.00, 0.92),
        _ellipse_mask(x, y, 182, 152, 23, 18, 0.00, 0.92),
    )
    height -= 0.085 * pit

    # The river cuts a deep channel through every plateau.
    river = 1.0 - _smoothstep(9.5, 25.0, _river_distance(x, y))
    height = height * (1.0 - river) + 0.052 * river

    # Slightly lower, broken ground at the outer map edge.
    edge_distance = min(x, y, MAP_SIZE - x, MAP_SIZE - y)
    edge = 1.0 - _smoothstep(5.0, 27.0, edge_distance)
    height -= 0.035 * edge
    return _clamp(height)


def _catmull_rom(
    points: tuple[tuple[float, float], ...],
    samples_per_segment: int = 10,
) -> list[tuple[float, float]]:
    if len(points) < 2:
        return list(points)
    padded = (points[0], *points, points[-1])
    result: list[tuple[float, float]] = []
    for index in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[index - 1 : index + 3]
        for sample in range(samples_per_segment):
            t = sample / samples_per_segment
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            result.append((x, y))
    result.append(points[-1])
    return result


def _offset_polyline(
    points: list[tuple[float, float]],
    offset: float,
) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points
    result: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        dx = following[0] - previous[0]
        dy = following[1] - previous[1]
        length = math.hypot(dx, dy) or 1.0
        nx = -dy / length
        ny = dx / length
        result.append((point[0] + nx * offset, point[1] + ny * offset))
    return result


def _color(value: str, alpha: int = 255) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


def _mix(first: QColor, second: QColor, amount: float) -> QColor:
    amount = _clamp(amount)
    return QColor(
        round(first.red() * (1 - amount) + second.red() * amount),
        round(first.green() * (1 - amount) + second.green() * amount),
        round(first.blue() * (1 - amount) + second.blue() * amount),
        round(first.alpha() * (1 - amount) + second.alpha() * amount),
    )


class MapProjection:
    """Straight top-down projection of the 256x256 Dota map."""

    def __init__(self, rect: QRectF) -> None:
        side = min(rect.width(), rect.height())
        self.rect = rect
        self.side = side
        self.scale = side / 500.0
        self.sx = side / MAP_SIZE
        self.sy = side / MAP_SIZE
        self.cx = rect.center().x()
        self.cy = rect.center().y()
        self.left = self.cx - side / 2
        self.top = self.cy - side / 2

    def project(self, x: float, y: float, z: float = 0.0) -> QPointF:
        del z
        return QPointF(self.left + x * self.sx, self.top + y * self.sy)

    def ground(self, x: float, y: float) -> QPointF:
        return self.project(x, y)


class DotaMapRenderer:
    """Cached, straight top-down 7.41 map board for the ward page."""

    def __init__(self) -> None:
        self._pixmap: QPixmap | None = None
        self._cache_key: tuple | None = None
        self._texture = QImage(str(resource_path("assets/dota_map.png")))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def paint(self, painter: QPainter, rect: QRectF, theme) -> None:
        if rect.width() < 24 or rect.height() < 24:
            return
        dpr = max(1.0, painter.device().devicePixelRatioF())
        size = QSize(max(1, round(rect.width())), max(1, round(rect.height())))
        key = (
            size.width(),
            size.height(),
            round(dpr, 2),
            theme.accent,
            theme.danger,
            theme.bg_alt,
        )
        if self._cache_key != key or self._pixmap is None:
            self._pixmap = self._render(size, dpr, theme)
            self._cache_key = key
        painter.drawPixmap(rect.topLeft(), self._pixmap)

    def feature_at(self, rect: QRectF, position: QPointF) -> str:
        projection = MapProjection(rect)
        threshold = max(8.0, rect.width() * 0.019)
        limit = threshold * threshold
        best = ""
        best_distance = limit
        for tower in TOWERS:
            point = projection.ground(tower.x, tower.y)
            distance = (point.x() - position.x()) ** 2 + (point.y() - position.y()) ** 2
            if distance <= best_distance:
                team = "Radiant" if tower.team == "radiant" else "Dire"
                best = f"{team} · {tower.lane} lane · Tier {tower.tier} tower"
                best_distance = distance
        for camp in CAMPS:
            point = projection.ground(camp.x, camp.y)
            distance = (point.x() - position.x()) ** 2 + (point.y() - position.y()) ** 2
            if distance <= best_distance:
                side = "Radiant" if camp.side == "radiant" else "Dire"
                best = f"{side} jungle · {camp.tier} camp"
                best_distance = distance
        return best

    # ------------------------------------------------------------------
    # Cached render
    # ------------------------------------------------------------------
    def _render(self, size: QSize, dpr: float, theme) -> QPixmap:
        pixmap = QPixmap(round(size.width() * dpr), round(size.height() * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(0, 0, size.width(), size.height())
        projection = MapProjection(rect)
        try:
            self._paint_backdrop(painter, rect, theme)
            self._paint_textured_map(painter, projection, theme)
            self._paint_camps(painter, projection)
            self._paint_towers(painter, projection)
            self._paint_labels(painter, projection, rect, theme)
            self._paint_vignette(painter, rect)
        finally:
            painter.end()
        return pixmap

    # ------------------------------------------------------------------
    # Terrain
    # ------------------------------------------------------------------
    def _paint_backdrop(self, painter: QPainter, rect: QRectF, theme) -> None:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor("#07100F"))
        gradient.setColorAt(0.48, QColor(theme.bg_alt))
        gradient.setColorAt(1.0, QColor("#060D11"))
        painter.fillRect(rect, gradient)

        accent = QColor(theme.accent)
        glow = QRadialGradient(rect.center(), rect.width() * 0.62)
        glow.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 18))
        glow.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.fillRect(rect, glow)

    def _paint_textured_map(
        self,
        painter: QPainter,
        projection: MapProjection,
        theme,
    ) -> None:
        if self._texture.isNull():
            painter.fillRect(projection.rect, QColor(theme.bg_alt))
            return
        board_rect = QRectF(
            projection.left,
            projection.top,
            projection.side,
            projection.side,
        )
        board = QPainterPath()
        board.addRoundedRect(board_rect, max(6.0, projection.scale * 10.0), max(6.0, projection.scale * 10.0))

        thickness = max(2.0, projection.scale * 4.0)
        shadow = QPainterPath(board)
        shadow.translate(0.0, thickness * 1.35)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 105))
        painter.drawPath(shadow)

        lower = QPainterPath(board)
        lower.translate(0.0, thickness)
        lower_gradient = QLinearGradient(lower.boundingRect().topLeft(), lower.boundingRect().bottomRight())
        lower_gradient.setColorAt(0.0, QColor("#0E1B18"))
        lower_gradient.setColorAt(1.0, QColor("#050B0A"))
        painter.setBrush(lower_gradient)
        painter.drawPath(lower)

        painter.save()
        painter.setClipPath(board)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawImage(board_rect, self._texture)
        painter.restore()

        # Keep the clean map from overpowering the dark application, then give
        # the straight board a crisp accent rim.
        painter.fillPath(board, QColor(4, 12, 11, 24))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 0, 0, 210), max(1.6, projection.scale * 1.7)))
        painter.drawPath(board)
        painter.setPen(QPen(QColor(theme.accent), max(0.8, projection.scale * 0.9)))
        painter.drawPath(board)

    def _paint_slab(self, painter: QPainter, projection: MapProjection, theme) -> None:
        corners = [
            projection.project(0, 0, 0.0),
            projection.project(MAP_SIZE, 0, 0.0),
            projection.project(MAP_SIZE, MAP_SIZE, 0.0),
            projection.project(0, MAP_SIZE, 0.0),
        ]
        slab = QPainterPath()
        slab.moveTo(corners[0])
        for corner in corners[1:]:
            slab.lineTo(corner)
        slab.closeSubpath()

        painter.save()
        painter.translate(0.012 * projection.scale * 500, 0.014 * projection.scale * 500)
        painter.fillPath(slab, QColor(0, 0, 0, 120))
        painter.restore()

        slab_gradient = QLinearGradient(corners[0], corners[2])
        slab_gradient.setColorAt(0.0, QColor("#101C18"))
        slab_gradient.setColorAt(1.0, QColor("#060B0A"))
        painter.setPen(QPen(QColor(255, 255, 255, 16), 1.0))
        painter.setBrush(slab_gradient)
        painter.drawPath(slab)

        accent = QColor(theme.accent)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 35), 1.0))
        painter.drawPath(slab)

    def _paint_terrain(self, painter: QPainter, projection: MapProjection) -> None:
        step = MAP_SIZE / GRID_CELLS
        heights = [
            [
                terrain_height(column * step + step / 2, row * step + step / 2)
                for column in range(GRID_CELLS)
            ]
            for row in range(GRID_CELLS)
        ]
        cells: list[tuple[float, int, int, float]] = []
        for row in range(GRID_CELLS):
            for column in range(GRID_CELLS):
                center = projection.project(
                    column * step + step / 2,
                    row * step + step / 2,
                    heights[row][column],
                )
                cells.append((center.y(), column, row, heights[row][column]))
        cells.sort(key=lambda item: item[0])

        for _, column, row, height in cells:
            self._paint_terrain_cell(painter, projection, heights, column, row, height, step)

    def _paint_terrain_cell(
        self,
        painter: QPainter,
        projection: MapProjection,
        heights: list[list[float]],
        column: int,
        row: int,
        height: float,
        step: float,
    ) -> None:
        x0 = column * step
        y0 = row * step
        x1 = x0 + step
        y1 = y0 + step

        south_z = heights[row + 1][column] if row + 1 < GRID_CELLS else 0.0
        east_z = heights[row][column + 1] if column + 1 < GRID_CELLS else 0.0

        p00 = projection.project(x0, y0, height)
        p10 = projection.project(x1, y0, height)
        p11 = projection.project(x1, y1, height)
        p01 = projection.project(x0, y1, height)

        # South-facing cliff wall.
        if height - south_z > 0.012:
            wall = QPainterPath()
            wall.moveTo(p01)
            wall.lineTo(p11)
            wall.lineTo(projection.project(x1, y1, south_z))
            wall.lineTo(projection.project(x0, y1, south_z))
            wall.closeSubpath()
            wall_color = self._wall_color(height, south_z, column, row, south=True)
            painter.setPen(QPen(wall_color.darker(125), 0.55))
            painter.setBrush(wall_color)
            painter.drawPath(wall)
            if height - south_z > 0.050:
                painter.setPen(QPen(QColor(181, 215, 190, 70), 0.65))
                painter.drawLine(p01, p11)

        # East-facing cliff wall.
        if height - east_z > 0.012:
            wall = QPainterPath()
            wall.moveTo(p11)
            wall.lineTo(p10)
            wall.lineTo(projection.project(x1, y0, east_z))
            wall.lineTo(projection.project(x1, y1, east_z))
            wall.closeSubpath()
            wall_color = self._wall_color(height, east_z, column, row, south=False)
            painter.setPen(QPen(wall_color.darker(125), 0.55))
            painter.setBrush(wall_color)
            painter.drawPath(wall)
            if height - east_z > 0.050:
                painter.setPen(QPen(QColor(181, 215, 190, 60), 0.65))
                painter.drawLine(p10, p11)

        top = QPainterPath()
        top.moveTo(p00)
        top.lineTo(p10)
        top.lineTo(p11)
        top.lineTo(p01)
        top.closeSubpath()
        fill = self._terrain_color(height, column, row, x0 + step / 2, y0 + step / 2)

        north_z = heights[row - 1][column] if row > 0 else height
        west_z = heights[row][column - 1] if column > 0 else height
        occluded = max(0.0, north_z - height) + max(0.0, west_z - height)
        exposed = max(0.0, height - north_z) + max(0.0, height - west_z)
        if occluded > 0.018:
            fill = fill.darker(100 + min(30, round(occluded * 78)))
        elif exposed > 0.018:
            fill = fill.lighter(100 + min(15, round(exposed * 38)))

        painter.setPen(QPen(fill, 0.45))
        painter.setBrush(fill)
        painter.drawPath(top)

        # A bright crest line after the top face makes cliffs readable at small sizes.
        crest = QPen(QColor(190, 225, 198, 92), max(0.55, 0.70 * projection.scale))
        painter.setPen(crest)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if height - south_z > 0.045:
            painter.drawLine(p01, p11)
        if height - east_z > 0.045:
            painter.drawLine(p10, p11)

    def _paint_cliff_shadows(
        self,
        painter: QPainter,
        projection: MapProjection,
    ) -> None:
        step = MAP_SIZE / GRID_CELLS
        heights = [
            [
                terrain_height(column * step + step / 2, row * step + step / 2)
                for column in range(GRID_CELLS)
            ]
            for row in range(GRID_CELLS)
        ]
        painter.setPen(Qt.PenStyle.NoPen)
        for row in range(GRID_CELLS - 1):
            for column in range(GRID_CELLS - 1):
                height = heights[row][column]
                south_z = heights[row + 1][column]
                east_z = heights[row][column + 1]
                if height - south_z > 0.055:
                    length = min(11.0, 3.0 + (height - south_z) * 22.0)
                    x0 = column * step
                    x1 = x0 + step
                    y = (row + 1) * step
                    shadow = QPainterPath()
                    shadow.moveTo(projection.project(x0, y, south_z + 0.006))
                    shadow.lineTo(projection.project(x1, y, south_z + 0.006))
                    shadow.lineTo(projection.project(x1, y + length, south_z + 0.006))
                    shadow.lineTo(projection.project(x0, y + length, south_z + 0.006))
                    shadow.closeSubpath()
                    alpha = min(70, round(24 + (height - south_z) * 85))
                    painter.setBrush(QColor(0, 0, 0, alpha))
                    painter.drawPath(shadow)
                if height - east_z > 0.055:
                    length = min(11.0, 3.0 + (height - east_z) * 22.0)
                    x = (column + 1) * step
                    y0 = row * step
                    y1 = y0 + step
                    shadow = QPainterPath()
                    shadow.moveTo(projection.project(x, y0, east_z + 0.006))
                    shadow.lineTo(projection.project(x, y1, east_z + 0.006))
                    shadow.lineTo(projection.project(x + length, y1, east_z + 0.006))
                    shadow.lineTo(projection.project(x + length, y0, east_z + 0.006))
                    shadow.closeSubpath()
                    alpha = min(60, round(20 + (height - east_z) * 75))
                    painter.setBrush(QColor(0, 0, 0, alpha))
                    painter.drawPath(shadow)

    def _paint_contours(
        self,
        painter: QPainter,
        projection: MapProjection,
    ) -> None:
        step = MAP_SIZE / GRID_CELLS
        vertices = [
            [
                terrain_height(column * step, row * step)
                for column in range(GRID_CELLS + 1)
            ]
            for row in range(GRID_CELLS + 1)
        ]
        levels = (0.18, 0.30, 0.42, 0.54, 0.66, 0.78, 0.88)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for level in levels:
            major = level in (0.30, 0.54, 0.78)
            color = QColor(196, 228, 203, 82 if major else 48)
            painter.setPen(QPen(color, 0.95 if major else 0.65))
            for row in range(GRID_CELLS):
                for column in range(GRID_CELLS):
                    x0 = column * step
                    y0 = row * step
                    x1 = x0 + step
                    y1 = y0 + step
                    h00 = vertices[row][column]
                    h10 = vertices[row][column + 1]
                    h11 = vertices[row + 1][column + 1]
                    h01 = vertices[row + 1][column]
                    edges = (
                        (x0, y0, h00, x1, y0, h10),
                        (x1, y0, h10, x1, y1, h11),
                        (x1, y1, h11, x0, y1, h01),
                        (x0, y1, h01, x0, y0, h00),
                    )
                    crossings: list[tuple[float, float]] = []
                    for ax, ay, ah, bx, by, bh in edges:
                        if (ah < level <= bh) or (bh < level <= ah):
                            span = bh - ah
                            t = 0.5 if abs(span) < 0.0001 else (level - ah) / span
                            crossings.append((ax + (bx - ax) * t, ay + (by - ay) * t))
                    if len(crossings) == 2:
                        painter.drawLine(
                            projection.project(*crossings[0], level),
                            projection.project(*crossings[1], level),
                        )
                    elif len(crossings) == 4:
                        painter.drawLine(
                            projection.project(*crossings[0], level),
                            projection.project(*crossings[1], level),
                        )
                        painter.drawLine(
                            projection.project(*crossings[2], level),
                            projection.project(*crossings[3], level),
                        )

    @staticmethod
    def _wall_color(
        height: float,
        neighbor: float,
        column: int,
        row: int,
        *,
        south: bool,
    ) -> QColor:
        drop = _clamp((height - neighbor) * 2.4)
        base = QColor("#3A463D") if south else QColor("#2B3530")
        rock = QColor("#68705F")
        color = _mix(base, rock, drop * 0.55)
        variation = ((column * 11 + row * 7) % 5 - 2) * 4
        return QColor(
            max(0, min(255, color.red() + variation)),
            max(0, min(255, color.green() + variation)),
            max(0, min(255, color.blue() + variation)),
        )

    @staticmethod
    def _terrain_color(
        height: float,
        column: int,
        row: int,
        x: float,
        y: float,
    ) -> QColor:
        if height < 0.16:
            color = QColor("#15383C")
        elif height < 0.31:
            color = QColor("#143A29")
        elif height < 0.48:
            color = QColor("#1D4C34")
        elif height < 0.66:
            color = QColor("#2A6645")
        elif height < 0.82:
            color = QColor("#3B8058")
        else:
            color = QColor("#4D9869")

        # The reference minimap has a green Radiant side and a cooler,
        # rocky Dire side. Tint only high ground so the river stays blue.
        river_line = 64.0 + x * 0.465
        if height > 0.29:
            if y > river_line:
                color = _mix(color, QColor("#327F54"), 0.22)
            else:
                color = _mix(color, QColor("#3B5B6D"), 0.45)

        radiant_base = math.hypot(x - 72, y - 184)
        dire_base = math.hypot(x - 184, y - 72)
        if height > 0.42 and radiant_base < 44:
            color = _mix(color, QColor("#4B9A62"), 0.16)
        if height > 0.42 and dire_base < 44:
            color = _mix(color, QColor("#813E4A"), 0.13)

        light = 0.84 + height * 0.25 + (((column * 13 + row * 7) % 5) - 2) * 0.012
        return QColor(
            max(0, min(255, round(color.red() * light))),
            max(0, min(255, round(color.green() * light))),
            max(0, min(255, round(color.blue() * light))),
        )

    # ------------------------------------------------------------------
    # River / lanes
    # ------------------------------------------------------------------
    def _paint_river(self, painter: QPainter, projection: MapProjection) -> None:
        centerline = _catmull_rom(RIVER_POINTS, 12)
        left = _offset_polyline(centerline, RIVER_HALF_WIDTH + 3.5)
        right = _offset_polyline(centerline, -(RIVER_HALF_WIDTH + 3.5))
        bank = self._project_polyline(projection, [*left, *reversed(right)], 0.061)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(4, 12, 16, 210))
        painter.drawPath(bank)

        left = _offset_polyline(centerline, RIVER_HALF_WIDTH)
        right = _offset_polyline(centerline, -RIVER_HALF_WIDTH)
        water = self._project_polyline(projection, [*left, *reversed(right)], 0.071)
        bounds = water.boundingRect()
        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        gradient.setColorAt(0.0, QColor("#0A2838"))
        gradient.setColorAt(0.45, QColor("#12526A"))
        gradient.setColorAt(1.0, QColor("#0B3448"))
        painter.setBrush(gradient)
        painter.drawPath(water)

        # Thin bank foam and a bright central current.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(116, 198, 222, 58), 1.0))
        painter.drawPath(water)
        current = [projection.project(x, y, 0.074) for x, y in centerline]
        painter.setPen(QPen(QColor(112, 205, 233, 58), max(1.0, projection.scale * 1.25)))
        painter.drawPolyline(current)

        random = Random(913)
        for index in range(2, len(centerline) - 2, 3):
            x, y = centerline[index]
            previous = centerline[index - 1]
            following = centerline[index + 1]
            dx = following[0] - previous[0]
            dy = following[1] - previous[1]
            length = math.hypot(dx, dy) or 1.0
            nx = -dy / length
            ny = dx / length
            side = -1 if random.random() < 0.5 else 1
            start = (x + nx * side * 3.0, y + ny * side * 3.0)
            end = (x + nx * side * 7.0 + dx * 0.4, y + ny * side * 7.0 + dy * 0.4)
            painter.setPen(QPen(QColor(154, 227, 244, 62), max(0.8, projection.scale)))
            painter.drawLine(
                projection.project(*start, 0.076),
                projection.project(*end, 0.076),
            )

    def _paint_lanes(self, painter: QPainter, projection: MapProjection) -> None:
        for lane in LANES:
            samples = _catmull_rom(lane, 12)
            path = QPainterPath()
            for index, (x, y) in enumerate(samples):
                point = projection.ground(x, y)
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(self._thick_pen("#07100D", 0.064, projection))
            painter.drawPath(path)
            painter.setPen(self._thick_pen("#3B5042", 0.045, projection))
            painter.drawPath(path)
            painter.setPen(self._thick_pen("#6C8067", 0.033, projection))
            painter.drawPath(path)
            painter.setPen(self._thick_pen("#A4B397", 0.005, projection))
            painter.drawPath(path)

    @staticmethod
    def _thick_pen(color: str, width: float, projection: MapProjection) -> QPen:
        pen = QPen(QColor(color), max(1.0, width * 500.0 * projection.scale))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return pen

    def _paint_bases(self, painter: QPainter, projection: MapProjection) -> None:
        scale = projection.scale
        for x, y, side in (
            (72, 184, "radiant"),
            (184, 72, "dire"),
        ):
            point = projection.ground(x, y)
            team = QColor(RADIANT_COLOR if side == "radiant" else DIRE_COLOR)
            glow = QRadialGradient(point, 34 * scale)
            glow.setColorAt(0.0, QColor(team.red(), team.green(), team.blue(), 58))
            glow.setColorAt(1.0, QColor(team.red(), team.green(), team.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(point, 34 * scale, 22 * scale)

            platform = QPainterPath()
            platform.addEllipse(point, 15.0 * scale, 8.0 * scale)
            painter.setBrush(QColor(16, 28, 23, 215))
            painter.setPen(QPen(QColor(team.red(), team.green(), team.blue(), 150), max(0.7, scale)))
            painter.drawPath(platform)
            painter.setBrush(QColor(team.red(), team.green(), team.blue(), 35))
            painter.drawEllipse(point, 11.0 * scale, 5.8 * scale)

            if side == "radiant":
                trunk_pen = QPen(QColor("#4C3A22"), max(1.2, 1.8 * scale))
                trunk_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(trunk_pen)
                painter.drawLine(
                    QPointF(point.x(), point.y() + 1 * scale),
                    QPointF(point.x(), point.y() - 13 * scale),
                )
                painter.setPen(Qt.PenStyle.NoPen)
                for radius, offset, shade in (
                    (8.5, 14.5, 22),
                    (6.6, 18.0, 34),
                    (4.5, 21.0, 48),
                ):
                    canopy = QPainterPath()
                    canopy.moveTo(point.x(), point.y() - (offset + 4.5) * scale)
                    canopy.lineTo(point.x() + radius * scale, point.y() - offset * scale)
                    canopy.lineTo(point.x() - radius * scale, point.y() - offset * scale)
                    canopy.closeSubpath()
                    painter.setBrush(QColor(32 + shade, 105 + shade, 61 + shade // 2, 235))
                    painter.drawPath(canopy)
            else:
                obelisk = QPainterPath()
                obelisk.moveTo(point.x() - 4.0 * scale, point.y() + 1.0 * scale)
                obelisk.lineTo(point.x() - 2.1 * scale, point.y() - 14.0 * scale)
                obelisk.lineTo(point.x(), point.y() - 20.0 * scale)
                obelisk.lineTo(point.x() + 2.1 * scale, point.y() - 14.0 * scale)
                obelisk.lineTo(point.x() + 4.0 * scale, point.y() + 1.0 * scale)
                obelisk.closeSubpath()
                painter.setPen(QPen(QColor(13, 16, 18, 235), max(0.8, scale)))
                painter.setBrush(QColor("#4A3238"))
                painter.drawPath(obelisk)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(team)
                painter.drawEllipse(
                    QPointF(point.x(), point.y() - 16.0 * scale),
                    2.4 * scale,
                    2.4 * scale,
                )
                painter.setBrush(QColor(255, 224, 225, 220))
                painter.drawEllipse(
                    QPointF(point.x(), point.y() - 16.0 * scale),
                    0.8 * scale,
                    0.8 * scale,
                )

    def _paint_bridges(self, painter: QPainter, projection: MapProjection) -> None:
        for bridge in BRIDGES:
            corners = self._rotated_rect(
                bridge.x,
                bridge.y,
                bridge.angle,
                bridge.length,
                bridge.width,
            )
            path = self._project_polyline(projection, corners, 0.090)
            painter.setPen(QPen(QColor(34, 25, 16, 230), max(1.0, projection.scale)))
            painter.setBrush(QColor("#796040"))
            painter.drawPath(path)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(48, 34, 20, 170), max(0.7, projection.scale * 0.7)))
            for fraction in (0.22, 0.42, 0.62, 0.82):
                x, y = self._point_on_rect(bridge.x, bridge.y, bridge.angle, bridge.length, fraction)
                half = bridge.width / 2
                angle = math.radians(bridge.angle)
                px, py = -math.sin(angle) * half, math.cos(angle) * half
                painter.drawLine(
                    projection.project(x - px, y - py, 0.092),
                    projection.project(x + px, y + py, 0.092),
                )

    # ------------------------------------------------------------------
    # Details
    # ------------------------------------------------------------------
    def _paint_ramps(self, painter: QPainter, projection: MapProjection) -> None:
        for ramp in RAMPS:
            corners = self._rotated_rect(
                ramp.x,
                ramp.y,
                ramp.angle,
                ramp.length,
                ramp.width,
            )
            projected = [
                projection.project(x, y, terrain_height(x, y) + 0.008)
                for x, y in corners
            ]
            path = QPainterPath()
            path.moveTo(projected[0])
            for point in projected[1:]:
                path.lineTo(point)
            path.closeSubpath()
            painter.setPen(QPen(QColor(52, 37, 21, 225), max(0.8, projection.scale)))
            painter.setBrush(QColor(151, 118, 73, 225))
            painter.drawPath(path)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(62, 43, 24, 190), max(0.6, projection.scale * 0.75)))
            for fraction in (0.30, 0.50, 0.70):
                x, y = self._point_on_rect(
                    ramp.x,
                    ramp.y,
                    ramp.angle,
                    ramp.length,
                    fraction,
                )
                half = ramp.width / 2 - 0.8
                angle = math.radians(ramp.angle)
                px, py = -math.sin(angle) * half, math.cos(angle) * half
                z = terrain_height(x, y) + 0.009
                painter.drawLine(
                    projection.project(x - px, y - py, z),
                    projection.project(x + px, y + py, z),
                )

            # Small bright chevron points uphill, so ramps read differently from bridges.
            angle = math.radians(ramp.angle)
            tip_x = ramp.x + math.cos(angle) * ramp.length * 0.38
            tip_y = ramp.y + math.sin(angle) * ramp.length * 0.38
            back_x = ramp.x + math.cos(angle) * ramp.length * 0.08
            back_y = ramp.y + math.sin(angle) * ramp.length * 0.08
            half = ramp.width * 0.32
            px, py = -math.sin(angle) * half, math.cos(angle) * half
            z_tip = terrain_height(tip_x, tip_y) + 0.011
            z_back = terrain_height(back_x, back_y) + 0.011
            painter.setPen(
                QPen(QColor(235, 212, 154, 205), max(0.8, projection.scale * 0.9))
            )
            painter.drawLine(
                projection.project(back_x - px, back_y - py, z_back),
                projection.project(tip_x, tip_y, z_tip),
            )
            painter.drawLine(
                projection.project(tip_x, tip_y, z_tip),
                projection.project(back_x + px, back_y + py, z_back),
            )

    def _paint_forest(self, painter: QPainter, projection: MapProjection) -> None:
        for x, y, size, shade in self._tree_points:
            point = projection.ground(x, y)
            scale = projection.scale
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 48))
            painter.drawEllipse(
                QPointF(point.x() + 1.1 * scale, point.y() + 1.4 * scale),
                2.7 * size * scale,
                1.3 * size * scale,
            )

            trunk = QPen(QColor("#3C3020"), max(0.6, 0.8 * scale))
            painter.setPen(trunk)
            painter.drawLine(
                QPointF(point.x(), point.y()),
                QPointF(point.x(), point.y() - 2.2 * size * scale),
            )
            painter.setPen(Qt.PenStyle.NoPen)
            canopy = QColor(24 + shade, 69 + shade, 43 + shade // 2, 235)
            painter.setBrush(canopy)
            for layer in range(3):
                width = (2.6 - layer * 0.45) * size * scale
                height = (2.3 - layer * 0.25) * size * scale
                top = point.y() - (2.2 + layer * 1.4) * size * scale
                path = QPainterPath()
                path.moveTo(point.x(), top)
                path.lineTo(point.x() + width, top + height)
                path.lineTo(point.x() - width, top + height)
                path.closeSubpath()
                painter.drawPath(path)

    def _paint_camps(self, painter: QPainter, projection: MapProjection) -> None:
        tier_meta = {
            "small": QColor("#A6D96A"),
            "medium": QColor("#F2CE57"),
            "hard": QColor("#F08B45"),
        }
        radius = max(3.6, projection.side * 0.0072)
        for camp in CAMPS:
            point = projection.ground(camp.x, camp.y)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 80))
            painter.drawEllipse(
                QPointF(point.x() + radius * 0.24, point.y() + radius * 0.32),
                radius * 1.18,
                radius * 0.78,
            )

            if camp.tier == "ancient":
                painter.setPen(QPen(QColor(18, 12, 8, 235), max(0.9, radius * 0.26)))
                painter.setBrush(QColor("#724421"))
                painter.drawEllipse(point, radius * 1.10, radius * 1.10)

                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor("#F0B878"), max(1.0, radius * 0.24)))
                painter.drawArc(
                    QRectF(
                        point.x() - radius * 0.54,
                        point.y() - radius * 0.60,
                        radius * 1.08,
                        radius * 1.20,
                    ),
                    40 * 16,
                    280 * 16,
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#FFE2B8"))
                painter.drawEllipse(point, radius * 0.22, radius * 0.22)
                continue

            tier_color = tier_meta[camp.tier]
            painter.setPen(QPen(QColor(8, 14, 14, 235), max(0.9, radius * 0.24)))
            painter.setBrush(QColor("#26332F"))
            painter.drawEllipse(point, radius, radius)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#F4F7ED"), max(1.1, radius * 0.28)))
            painter.drawEllipse(point, radius * 0.68, radius * 0.68)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(tier_color)
            painter.drawEllipse(point, radius * 0.26, radius * 0.26)

    def _paint_towers(self, painter: QPainter, projection: MapProjection) -> None:
        half = max(5.4, projection.side * 0.0105)
        for tower in TOWERS:
            point = projection.ground(tower.x, tower.y)
            team_color = QColor(RADIANT_COLOR if tower.team == "radiant" else DIRE_COLOR)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 90))
            painter.drawRoundedRect(
                QRectF(
                    point.x() - half + half * 0.34,
                    point.y() - half + half * 0.42,
                    half * 2.0,
                    half * 2.0,
                ),
                half * 0.42,
                half * 0.42,
            )

            painter.setPen(QPen(QColor(7, 12, 10, 240), max(0.9, half * 0.22)))
            painter.setBrush(QColor("#0C1512"))
            painter.drawRoundedRect(
                QRectF(point.x() - half, point.y() - half, half * 2.0, half * 2.0),
                half * 0.42,
                half * 0.42,
            )

            inset = max(1.0, half * 0.22)
            inner = QRectF(
                point.x() - half + inset,
                point.y() - half + inset,
                (half - inset) * 2.0,
                (half - inset) * 2.0,
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(team_color)
            painter.drawRoundedRect(inner, half * 0.30, half * 0.30)

            painter.setBrush(QColor(255, 255, 255, 58))
            painter.drawRoundedRect(
                QRectF(
                    inner.left() + inset * 0.42,
                    inner.top() + inset * 0.42,
                    inner.width() * 0.60,
                    inner.height() * 0.24,
                ),
                half * 0.16,
                half * 0.16,
            )

            if tower.tier == 4:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 215), max(0.8, half * 0.16)))
                painter.drawRoundedRect(
                    QRectF(
                        point.x() - half * 0.58,
                        point.y() - half * 0.58,
                        half * 1.16,
                        half * 1.16,
                    ),
                    half * 0.18,
                    half * 0.18,
                )

    def _paint_runes(self, painter: QPainter, projection: MapProjection) -> None:
        for x, y in RUNE_POINTS:
            point = projection.ground(x, y)
            scale = projection.scale
            size = 4.1 * scale
            glow = QRadialGradient(point, 8.0 * scale)
            glow.setColorAt(0.0, QColor(151, 123, 255, 100))
            glow.setColorAt(1.0, QColor(151, 123, 255, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(point, 8.0 * scale, 8.0 * scale)
            path = QPainterPath()
            path.moveTo(point.x(), point.y() - size)
            path.lineTo(point.x() + size, point.y())
            path.lineTo(point.x(), point.y() + size)
            path.lineTo(point.x() - size, point.y())
            path.closeSubpath()
            painter.setPen(QPen(QColor(17, 13, 30, 220), max(0.7, scale * 0.8)))
            painter.setBrush(QColor("#B29BFF"))
            painter.drawPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(251, 248, 255, 240))
            painter.drawEllipse(point, 1.05 * scale, 1.05 * scale)

    def _paint_roshan(self, painter: QPainter, projection: MapProjection) -> None:
        for x, y in ROSHAN_PITS:
            point = projection.ground(x, y)
            scale = projection.scale
            painter.setPen(QPen(QColor(20, 26, 24, 220), max(0.8, scale)))
            painter.setBrush(QColor(22, 31, 28, 235))
            painter.drawEllipse(point, 10.0 * scale, 5.2 * scale)
            painter.setBrush(QColor(56, 48, 38, 190))
            painter.drawEllipse(
                QPointF(point.x(), point.y() - 0.7 * scale),
                7.7 * scale,
                3.7 * scale,
            )
            painter.setPen(QPen(QColor(158, 92, 77, 150), max(0.7, scale * 0.8)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(point, 6.1 * scale, 2.8 * scale)

            font = QFont("Bahnschrift", max(5, round(5.0 * scale)))
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.setPen(QColor(211, 171, 141, 145))
            painter.drawText(
                QRectF(point.x() - 24 * scale, point.y() + 7 * scale, 48 * scale, 10 * scale),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                "ROSHAN",
            )

    def _paint_shrines(self, painter: QPainter, projection: MapProjection) -> None:
        for x, y, side in SHRINE_POINTS:
            point = projection.ground(x, y)
            scale = projection.scale
            color = QColor(RADIANT_COLOR if side == "radiant" else DIRE_COLOR)
            painter.setPen(QPen(QColor(8, 14, 12, 220), max(0.7, scale * 0.8)))
            painter.setBrush(QColor(42, 58, 50))
            painter.drawRect(
                QRectF(
                    point.x() - 3.2 * scale,
                    point.y() - 5.5 * scale,
                    6.4 * scale,
                    5.5 * scale,
                )
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(
                QPointF(point.x(), point.y() - 6.0 * scale),
                1.8 * scale,
                1.8 * scale,
            )

    # ------------------------------------------------------------------
    # Labels / finishing
    # ------------------------------------------------------------------
    def _paint_labels(
        self,
        painter: QPainter,
        projection: MapProjection,
        rect: QRectF,
        theme,
    ) -> None:
        scale = projection.scale
        font = QFont("Bahnschrift", max(6, round(6.3 * scale)))
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)

        for x, y, text, color in (
            (27, 229, "RADIANT", RADIANT_COLOR),
            (228, 27, "DIRE", DIRE_COLOR),
        ):
            point = projection.ground(x, y)
            badge = QRectF(
                point.x() - 31 * scale,
                point.y() - 7.5 * scale,
                62 * scale,
                15 * scale,
            )
            badge_path = QPainterPath()
            badge_path.addRoundedRect(badge, 5 * scale, 5 * scale)
            painter.fillPath(badge_path, QColor(3, 10, 9, 185))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(color), 0.75))
            painter.drawPath(badge_path)
            painter.setPen(QColor(color))
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, text)

        # Small patch pill in an empty corner of the rounded panel.
        pill = QRectF(rect.left() + 12, rect.top() + 12, 84 * scale, 20 * scale)
        pill_path = QPainterPath()
        pill_path.addRoundedRect(pill, 7 * scale, 7 * scale)
        painter.fillPath(pill_path, QColor(4, 12, 11, 170))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(theme.accent), 0.8))
        painter.drawPath(pill_path)
        badge_font = QFont("Bahnschrift", max(5, round(5.8 * scale)))
        badge_font.setWeight(QFont.Weight.DemiBold)
        badge_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0 * scale)
        painter.setFont(badge_font)
        painter.setPen(QColor(theme.accent))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, "7.41 MAP")

    def _paint_vignette(self, painter: QPainter, rect: QRectF) -> None:
        vignette = QRadialGradient(rect.center(), rect.width() * 0.72)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.64, QColor(0, 0, 0, 12))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 105))
        painter.fillRect(rect, vignette)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def _make_trees(self) -> list[tuple[float, float, float, int]]:
        random = Random(20261103)
        trees: list[tuple[float, float, float, int]] = []
        for cx, cy, rx, ry, count in FOREST_CLUSTERS:
            placed = 0
            attempts = 0
            while placed < count and attempts < count * 14:
                attempts += 1
                angle = random.random() * math.tau
                radius = math.sqrt(random.random())
                x = cx + math.cos(angle) * rx * radius
                y = cy + math.sin(angle) * ry * radius
                if not (5.0 <= x <= 251.0 and 5.0 <= y <= 251.0):
                    continue
                if _river_distance(x, y) < 17.0:
                    continue
                if min(
                    _polyline_distance(x, y, lane)
                    for lane in LANES
                ) < 10.0:
                    continue
                if any(math.hypot(x - tower.x, y - tower.y) < 11.0 for tower in TOWERS):
                    continue
                if any(math.hypot(x - camp.x, y - camp.y) < 10.0 for camp in CAMPS):
                    continue
                if any(math.hypot(x - rx0, y - ry0) < 15.0 for rx0, ry0 in RUNE_POINTS):
                    continue
                if math.hypot(x - 72, y - 184) < 24 or math.hypot(x - 184, y - 72) < 24:
                    continue
                trees.append((x, y, 0.70 + random.random() * 0.55, random.randint(0, 22)))
                placed += 1
        return trees

    @staticmethod
    def _rotated_rect(
        cx: float,
        cy: float,
        angle: float,
        length: float,
        width: float,
    ) -> list[tuple[float, float]]:
        radians = math.radians(angle)
        dx = math.cos(radians) * length / 2
        dy = math.sin(radians) * length / 2
        px = -math.sin(radians) * width / 2
        py = math.cos(radians) * width / 2
        return [
            (cx - dx - px, cy - dy - py),
            (cx + dx - px, cy + dy - py),
            (cx + dx + px, cy + dy + py),
            (cx - dx + px, cy - dy + py),
        ]

    @staticmethod
    def _point_on_rect(
        cx: float,
        cy: float,
        angle: float,
        length: float,
        fraction: float,
    ) -> tuple[float, float]:
        radians = math.radians(angle)
        offset = (fraction - 0.5) * length
        return cx + math.cos(radians) * offset, cy + math.sin(radians) * offset

    @staticmethod
    def _project_polyline(
        projection: MapProjection,
        points: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        z: float,
    ) -> QPainterPath:
        path = QPainterPath()
        for index, (x, y) in enumerate(points):
            point = projection.project(x, y, z)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        return path
