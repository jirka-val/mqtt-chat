"""Bocni panel se seznamem uzivatelu, scrollovatelny, online nahore."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from .theme import OFFLINE, ONLINE, PANEL, apply_card_shadow, set_flat_background

DOT_SIZE = 9


class UserRow(QFrame):
    """Radek uzivatele v seznamu - klikem vybere prijemce pro soukromou zpravu."""

    clicked = pyqtSignal(str)

    def __init__(self, identity: str):
        super().__init__()
        self.identity = identity
        self.setObjectName("userRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.identity)
        super().mousePressEvent(event)


class UserListView(QFrame):
    user_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        apply_card_shadow(self)
        self.setFixedWidth(190)

        self.statuses: dict[str, str] = {}

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(100)
        self._render_timer.timeout.connect(self._render)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 16, 20)
        outer.setSpacing(10)

        heading = QLabel("UZIVATELE")
        heading.setObjectName("fieldLabel")
        outer.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        set_flat_background(scroll.viewport(), PANEL)

        content = QWidget()
        set_flat_background(content, PANEL)
        self.rows_layout = QVBoxLayout(content)
        self.rows_layout.setContentsMargins(0, 0, 4, 0)
        self.rows_layout.setSpacing(8)
        self.rows_layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def set_status(self, identity: str, status: str) -> None:
        if self.statuses.get(identity) == status:
            return

        self.statuses[identity] = status

        # stavy chodi po stovkach naraz, prekreslime az po poslednim
        self._render_timer.start()

    def _render(self) -> None:
        # posledni polozka je stretch, ten necháme, zbytek zahodime
        while self.rows_layout.count() > 1:
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

        online = sorted(u for u, s in self.statuses.items() if s == "online")
        offline = sorted(u for u, s in self.statuses.items() if s != "online")

        position = 0
        for identity in online:
            self.rows_layout.insertWidget(position, self._build_row(identity, online=True))
            position += 1
        for identity in offline:
            self.rows_layout.insertWidget(position, self._build_row(identity, online=False))
            position += 1

    def _build_row(self, identity: str, online: bool) -> QWidget:
        row = UserRow(identity)
        row.clicked.connect(self.user_selected.emit)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(DOT_SIZE, DOT_SIZE)
        color = ONLINE if online else OFFLINE
        dot.setStyleSheet(f"background-color: {color}; border-radius: {DOT_SIZE // 2}px;")
        layout.addWidget(dot)

        name_label = QLabel(identity)
        layout.addWidget(name_label)
        layout.addStretch(1)
        return row
