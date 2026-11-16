from __future__ import annotations

from dataclasses import dataclass
from string import Template

from PySide6.QtGui import QColor


@dataclass(frozen=True, slots=True)
class Theme:
    key: str
    name: str
    subtitle: str
    accent: str
    accent_light: str
    accent_dark: str
    accent_deep: str
    danger: str
    warning: str

    bg: str = "#080D12"
    bg_alt: str = "#0B1117"
    surface: str = "#0F1821"
    surface_alt: str = "#13202A"
    surface_high: str = "#192A35"
    border: str = "#1D2C37"
    border_strong: str = "#2B4050"
    text: str = "#EAF2F6"
    text_muted: str = "#8CA1AF"
    text_dim: str = "#5F7482"


THEMES: dict[str, Theme] = {
    "emerald": Theme(
        key="emerald",
        name="Изумруд",
        subtitle="Классический Dota-стиль",
        accent="#39DFA3",
        accent_light="#69EDC1",
        accent_dark="#1DAE7C",
        accent_deep="#0C3A2B",
        danger="#FF6B72",
        warning="#F2B65A",
    ),
    "amber": Theme(
        key="amber",
        name="Янтарь",
        subtitle="Тёплый турнирный акцент",
        accent="#F5B84B",
        accent_light="#FFD277",
        accent_dark="#CE901F",
        accent_deep="#3E2B0A",
        danger="#FF6B72",
        warning="#F5B84B",
    ),
    "crimson": Theme(
        key="crimson",
        name="Кармин",
        subtitle="Агрессивный боевой стиль",
        accent="#FF6577",
        accent_light="#FF92A0",
        accent_dark="#CE3D50",
        accent_deep="#3E1119",
        danger="#FF7B7B",
        warning="#F2B65A",
    ),
}

_current_theme = THEMES["emerald"]


def current_theme() -> Theme:
    return _current_theme


def set_current_theme(key: str) -> Theme:
    global _current_theme
    _current_theme = THEMES.get(key, THEMES["emerald"])
    return _current_theme


def rgba(color: str, alpha: float) -> str:
    """CSS rgba() для QSS. alpha — 0..1."""
    c = QColor(color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {max(0, min(255, round(alpha * 255)))})"


def blend(color_a: str, color_b: str, amount: float) -> str:
    a = QColor(color_a)
    b = QColor(color_b)
    t = max(0.0, min(1.0, amount))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    ).name()


_QSS = Template(
    """
    * {
        outline: none;
    }
    QWidget {
        color: $text;
        font-family: "Segoe UI";
        font-size: 10pt;
        background: transparent;
    }
    QMainWindow, QDialog {
        background-color: $bg;
    }
    QMessageBox {
        background-color: $surface;
    }
    QToolTip {
        color: $text;
        background-color: $surface_high;
        border: 1px solid $border_strong;
        padding: 6px 8px;
        border-radius: 6px;
    }

    QFrame#Card {
        background-color: $surface;
        border: 1px solid $border;
        border-radius: 16px;
    }
    QFrame#SoftCard {
        background-color: $surface_alt;
        border: 1px solid $border;
        border-radius: 12px;
    }
    QFrame#Divider {
        background-color: $border;
        border: none;
        max-height: 1px;
        min-height: 1px;
    }
    QFrame#Toast {
        background-color: $surface_high;
        border: 1px solid $border_strong;
        border-radius: 12px;
    }

    QLabel {
        background: transparent;
    }
    QLabel#AppTitle {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 14pt;
        font-weight: 700;
    }
    QLabel#AppSubtitle {
        color: $text_dim;
        font-size: 7.5pt;
        font-weight: 600;
    }
    QLabel#PageTitle {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 23pt;
        font-weight: 600;
    }
    QLabel#PageSubtitle {
        color: $text_muted;
        font-size: 10pt;
    }
    QLabel#SectionTitle {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 13pt;
        font-weight: 600;
    }
    QLabel#CardLabel {
        color: $text_muted;
        font-size: 7.5pt;
        font-weight: 700;
    }
    QLabel#StatValue {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 27pt;
        font-weight: 600;
    }
    QLabel#StatValueSmall {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 21pt;
        font-weight: 600;
    }
    QLabel#StatHint {
        color: $text_dim;
        font-size: 8.5pt;
    }
    QLabel#Muted {
        color: $text_muted;
        font-size: 9pt;
    }
    QLabel#Dim {
        color: $text_dim;
        font-size: 8.5pt;
    }
    QLabel#Accent {
        color: $accent;
    }
    QLabel#Danger {
        color: $danger;
    }
    QLabel#ProfileName {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 25pt;
        font-weight: 600;
    }
    QLabel#ProfileMeta {
        color: $text_muted;
        font-size: 9pt;
    }
    QLabel#ProfileCaption {
        color: $text_dim;
        font-size: 8pt;
        font-weight: 600;
    }
    QLabel#AccentDot {
        background-color: $accent;
        border-radius: 3px;
    }
    QLabel#WarningDot {
        background-color: $warning;
        border-radius: 3px;
    }
    QLabel#DangerDot {
        background-color: $danger;
        border-radius: 3px;
    }
    QLabel#WinBadge {
        color: $accent;
        background-color: $accent_soft;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 8pt;
        font-weight: 700;
    }
    QLabel#LossBadge {
        color: $danger;
        background-color: $danger_soft;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 8pt;
        font-weight: 700;
    }
    QLabel#MetaPill {
        color: $text_muted;
        background-color: $surface_alt;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 8pt;
        font-weight: 600;
    }
    QLabel#RankPill {
        color: $accent;
        background-color: $accent_deep;
        border: 1px solid $accent_border;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 8pt;
        font-weight: 700;
    }
    QLabel#LivePill {
        color: $text_muted;
        background-color: $bg_alt;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 8pt;
        font-weight: 600;
    }
    QLabel#WinRateHigh {
        color: $accent;
        font-family: "Bahnschrift";
        font-size: 12pt;
        font-weight: 600;
    }
    QLabel#WinRateLow {
        color: $danger;
        font-family: "Bahnschrift";
        font-size: 12pt;
        font-weight: 600;
    }
    QLabel#HeroName {
        color: $text;
        font-size: 10pt;
        font-weight: 600;
    }
    QLabel#HeroMeta {
        color: $text_dim;
        font-size: 8pt;
    }
    QLabel#RankNumber {
        color: $text_dim;
        font-family: "Bahnschrift";
        font-size: 10pt;
        font-weight: 600;
    }
    QLabel#RankNumberTop {
        color: $accent;
        font-family: "Bahnschrift";
        font-size: 10pt;
        font-weight: 700;
    }
    QLabel#SetupEyebrow {
        color: $accent;
        font-size: 8pt;
        font-weight: 700;
    }
    QLabel#SetupTitle {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 25pt;
        font-weight: 600;
    }
    QLabel#SetupLead {
        color: $text_muted;
        font-size: 10pt;
        line-height: 145%;
    }
    QLabel#FieldLabel {
        color: $text;
        font-size: 9pt;
        font-weight: 600;
    }
    QLabel#FieldHint {
        color: $text_dim;
        font-size: 8pt;
    }
    QLabel#FieldError {
        color: $danger;
        font-size: 8.5pt;
    }
    QLabel#BrandTitle {
        color: #F5FBF8;
        font-family: "Bahnschrift";
        font-size: 27pt;
        font-weight: 700;
    }
    QLabel#BrandSubtitle {
        color: #A9C4B9;
        font-size: 10pt;
    }
    QLabel#BrandFeatureTitle {
        color: #F5FBF8;
        font-size: 9.5pt;
        font-weight: 600;
    }
    QLabel#BrandFeatureText {
        color: #8EABA0;
        font-size: 8.5pt;
    }
    QLabel#BrandFooter {
        color: #6F897F;
        font-size: 8pt;
    }
    QLabel#FormDotWin {
        background-color: $accent;
        border-radius: 4px;
    }
    QLabel#FormDotLoss {
        background-color: $danger;
        border-radius: 4px;
    }

    QPushButton {
        min-height: 36px;
        padding: 0 16px;
        border: none;
        border-radius: 9px;
        color: $text;
        background-color: transparent;
        font-size: 9.5pt;
        font-weight: 600;
    }
    QPushButton#Primary {
        color: #06120D;
        background-color: $accent;
    }
    QPushButton#Primary:hover {
        background-color: $accent_light;
    }
    QPushButton#Primary:pressed {
        background-color: $accent_dark;
    }
    QPushButton#Primary:disabled {
        color: #65766E;
        background-color: #1D2F27;
    }
    QPushButton#Ghost {
        color: $text;
        background-color: $surface_alt;
        border: 1px solid $border_strong;
    }
    QPushButton#Ghost:hover {
        color: $accent;
        border-color: $accent_border;
        background-color: $surface_high;
    }
    QPushButton#Ghost:pressed {
        background-color: $surface;
    }
    QPushButton#Ghost:disabled {
        color: $text_dim;
        border-color: $border;
        background-color: $surface;
    }
    QPushButton#Subtle {
        color: $text_muted;
        background-color: transparent;
        border: 1px solid transparent;
    }
    QPushButton#Subtle:hover {
        color: $text;
        background-color: $surface_alt;
    }
    QPushButton#DangerGhost {
        color: $danger;
        background-color: transparent;
        border: 1px solid $danger_soft;
    }
    QPushButton#DangerGhost:hover {
        background-color: $danger_soft;
    }
    QPushButton#NavButton {
        min-height: 51px;
        padding: 0 17px;
        color: $text_muted;
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        font-size: 9.5pt;
        font-weight: 600;
    }
    QPushButton#NavButton:hover {
        color: $text;
        background-color: $surface;
    }
    QPushButton#NavButton:checked {
        color: $accent;
        border-bottom: 2px solid $accent;
        background-color: transparent;
    }
    QPushButton#Chip {
        min-height: 30px;
        padding: 0 12px;
        color: $text_muted;
        background-color: $surface_alt;
        border: 1px solid $border;
        border-radius: 7px;
        font-size: 8pt;
        font-weight: 600;
    }
    QPushButton#Chip:hover {
        color: $text;
        border-color: $border_strong;
    }
    QPushButton#Chip:checked {
        color: $accent;
        background-color: $accent_deep;
        border-color: $accent_border;
    }
    QPushButton#Chip:disabled {
        color: $text_dim;
        background-color: $surface;
        border-color: $border;
    }
    QPushButton#IconButton {
        min-width: 38px;
        max-width: 38px;
        min-height: 38px;
        max-height: 38px;
        padding: 0;
        color: $text_muted;
        background-color: $surface_alt;
        border: 1px solid $border;
        border-radius: 9px;
    }
    QPushButton#IconButton:hover {
        color: $accent;
        border-color: $accent_border;
        background-color: $surface_high;
    }

    QLineEdit {
        min-height: 44px;
        padding: 0 13px;
        color: $text;
        background-color: $bg_alt;
        border: 1px solid $border_strong;
        border-radius: 9px;
        selection-background-color: $accent;
        selection-color: #06120D;
    }
    QLineEdit:focus {
        border: 1px solid $accent;
        background-color: $surface;
    }
    QLineEdit[invalid="true"] {
        border: 1px solid $danger;
    }
    QLineEdit:disabled {
        color: $text_dim;
    }

    QTableWidget {
        color: $text;
        background-color: transparent;
        alternate-background-color: $surface;
        border: none;
        gridline-color: transparent;
        selection-background-color: $accent_soft;
        selection-color: $text;
    }
    QTableWidget::item {
        padding: 0 10px;
        border: none;
        border-bottom: 1px solid $border;
    }
    QTableWidget::item:hover {
        background-color: $hover_row;
    }
    QTableWidget::item:selected {
        background-color: $accent_soft;
        color: $text;
    }
    QHeaderView {
        background-color: transparent;
    }
    QHeaderView::section {
        color: $text_dim;
        background-color: transparent;
        border: none;
        border-bottom: 1px solid $border;
        padding: 8px 10px;
        font-size: 7.5pt;
        font-weight: 700;
    }
    QHeaderView::section:first {
        padding-left: 4px;
    }
    QTableCornerButton::section {
        background-color: transparent;
        border: none;
    }

    QListWidget#WardMatchList, QListWidget#WardList {
        background-color: transparent;
        border: none;
        outline: none;
    }
    QListWidget#WardMatchList::item, QListWidget#WardList::item {
        background-color: transparent;
        border: none;
        border-bottom: 1px solid $border;
        padding: 0;
    }
    QListWidget#WardList::item {
        padding: 4px 3px;
        color: $text_muted;
    }
    QListWidget#WardMatchList::item:hover, QListWidget#WardList::item:hover {
        background-color: $hover_row;
    }
    QListWidget#WardMatchList::item:selected, QListWidget#WardList::item:selected {
        background-color: $accent_soft;
        color: $text;
        border-bottom: 1px solid $accent_border;
    }

    QSlider::groove:horizontal {
        height: 4px;
        background-color: $surface_high;
        border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        background-color: $accent;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
        background-color: $accent;
    }
    QSlider::handle:horizontal:hover {
        background-color: $accent_light;
    }
    QSlider::groove:horizontal:disabled {
        background-color: $border;
    }
    QSlider::sub-page:horizontal:disabled {
        background-color: $border_strong;
    }
    QSlider::handle:horizontal:disabled {
        background-color: $border_strong;
    }
    QCheckBox#WardTimeCheck {
        color: $text_muted;
        font-size: 8pt;
        spacing: 6px;
    }
    QLabel#WardTime {
        color: $accent;
        font-family: "Bahnschrift";
        font-size: 9pt;
        font-weight: 600;
    }

    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollArea > QWidget > QWidget {
        background-color: transparent;
    }
    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 3px 0;
    }
    QScrollBar::handle:vertical {
        background: $border_strong;
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: $text_dim;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
        background: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 10px;
    }
    QScrollBar::handle:horizontal {
        background: $border_strong;
        min-width: 30px;
        border-radius: 4px;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
        background: none;
    }

    QProgressBar {
        min-height: 6px;
        max-height: 6px;
        background-color: $surface_high;
        border: none;
        border-radius: 3px;
    }
    QProgressBar::chunk {
        background-color: $accent;
        border-radius: 3px;
    }
    QProgressBar#DangerBar::chunk {
        background-color: $danger;
    }
    QProgressBar#ThinLoader {
        min-height: 2px;
        max-height: 2px;
        background-color: transparent;
        border: none;
        border-radius: 0;
    }
    QProgressBar#ThinLoader::chunk {
        background-color: $accent;
        border-radius: 0;
    }

    QWidget#Header {
        background-color: $bg_alt;
        border-bottom: 1px solid $border;
    }
    QWidget#NavBar {
        background-color: $bg_alt;
        border-bottom: 1px solid $border;
    }
    QWidget#Footer {
        background-color: $bg;
        border-top: 1px solid $border;
    }
    QWidget#SetupRight {
        background-color: $bg_alt;
    }
    QFrame#SetupCard {
        background-color: $surface;
        border: 1px solid $border;
        border-radius: 16px;
    }
    QFrame#ErrorIcon {
        background-color: $danger_soft;
        border: 1px solid $danger_border;
        border-radius: 38px;
    }
    QLabel#ErrorTitle {
        color: $text;
        font-family: "Bahnschrift";
        font-size: 21pt;
        font-weight: 600;
    }
    QLabel#ErrorText {
        color: $text_muted;
        font-size: 9.5pt;
    }
    QLabel#ErrorGlyph {
        color: $danger;
        font-family: "Bahnschrift";
        font-size: 27pt;
        font-weight: 600;
    }

    QCheckBox {
        color: $text_muted;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid $border_strong;
        border-radius: 4px;
        background-color: $bg_alt;
    }
    QCheckBox::indicator:checked {
        background-color: $accent;
        border-color: $accent;
    }
    """
)


def apply_theme(app, key: str) -> Theme:
    """Применяет QSS и перерисовывает кастомные виджеты."""
    theme = set_current_theme(key)
    app.setStyleSheet(build_stylesheet(theme))
    for widget in app.allWidgets():
        widget.update()
    return theme


def build_stylesheet(theme: Theme | None = None) -> str:
    t = theme or current_theme()
    return _QSS.substitute(
        bg=t.bg,
        bg_alt=t.bg_alt,
        surface=t.surface,
        surface_alt=t.surface_alt,
        surface_high=t.surface_high,
        border=t.border,
        border_strong=t.border_strong,
        text=t.text,
        text_muted=t.text_muted,
        text_dim=t.text_dim,
        accent=t.accent,
        accent_light=t.accent_light,
        accent_dark=t.accent_dark,
        accent_deep=t.accent_deep,
        accent_soft=rgba(t.accent, 0.12),
        accent_border=rgba(t.accent, 0.34),
        danger=t.danger,
        danger_soft=rgba(t.danger, 0.12),
        danger_border=rgba(t.danger, 0.3),
        warning=t.warning,
        hover_row=rgba(t.accent, 0.035),
    )
