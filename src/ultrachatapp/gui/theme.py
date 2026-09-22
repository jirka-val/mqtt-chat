"""Barvy, globalni QSS a pomocny stin pro cele okno - svetle, moderni ladeni."""
from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget

BG = "#e9ecf9"
PANEL = "#ffffff"
PANEL_ALT = "#f1f2fa"
BORDER = "#e3e5f2"
ACCENT = "#6c63ff"
ACCENT_HOVER = "#5a52e6"
TEXT = "#242640"
MUTED = "#8a8da3"
ERROR = "#e5484d"
ONLINE = "#2ecc84"
OFFLINE = "#c7c9db"


def apply_card_shadow(widget: QWidget, blur: int = 30, y_offset: int = 10) -> None:
    """Prida pod kartu jemny stin, aby pusobila jako bublina nad pozadim."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(36, 38, 64, 40))
    widget.setGraphicsEffect(effect)


def set_flat_background(widget: QWidget, color: str) -> None:
    """Vybarvi plochu widgetu pres QPalette - na rozdil od setStyleSheet()
    tim nerozbije QSS styl vnorenych potomku (napr. bublin zprav)."""
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), QColor(color))
    widget.setPalette(palette)
    widget.setAutoFillBackground(True)


STYLESHEET = f"""
QWidget {{
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 10pt;
}}

QMainWindow, QStackedWidget {{
    background-color: {BG};
}}

QLineEdit {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 9px 12px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}

QPushButton#accent {{
    background-color: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton#accent:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#accent:pressed {{ background-color: {ACCENT_HOVER}; }}

QLabel#title {{ font-size: 19pt; font-weight: 700; color: {TEXT}; }}
QLabel#fieldLabel {{ color: {MUTED}; font-size: 9pt; }}
QLabel#muted {{ color: {MUTED}; font-size: 9pt; }}
QLabel#error {{ color: {ERROR}; }}

QFrame#loginCard {{
    background-color: {PANEL};
    border-radius: 22px;
}}

QFrame#userRow {{
    background-color: transparent;
    border-radius: 8px;
}}
QFrame#userRow:hover {{
    background-color: {PANEL_ALT};
}}

QFrame#card {{
    background-color: {PANEL};
    border-radius: 22px;
}}

QFrame#divider {{
    background-color: {BORDER};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

QScrollArea {{ border: none; background: transparent; }}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QFrame#bubbleOwn {{
    background-color: {ACCENT};
    border-radius: 14px;
}}
QFrame#bubbleOwn QLabel {{ color: #ffffff; background: transparent; }}
QFrame#bubbleOwn QLabel#bubbleMeta {{ color: rgba(255, 255, 255, 0.75); }}

QFrame#bubbleAll {{
    background-color: {PANEL_ALT};
    border-radius: 14px;
}}
QFrame#bubbleAll QLabel {{ background: transparent; }}

QFrame#bubblePrivate {{
    background-color: {PANEL_ALT};
    border: 1px solid {ACCENT};
    border-radius: 14px;
}}
QFrame#bubblePrivate QLabel {{ background: transparent; }}

QLabel#bubbleMeta {{ color: {MUTED}; font-size: 8pt; font-weight: 600; }}
QLabel#bubbleBody {{ font-size: 10pt; }}
"""
