"""Chatovaci obrazovka - zoznam bublin se zpravami a radek pro psani."""
from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .message_bubble import MessageBubble
from .theme import PANEL, apply_card_shadow, set_flat_background


class ChatView(QFrame):
    def __init__(self, identity: str, on_send: Callable[[str, str], None]):
        super().__init__()
        self.setObjectName("card")
        apply_card_shadow(self)
        self.on_send = on_send

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(12)

        outer.addLayout(self._build_header(identity))
        outer.addWidget(self._build_divider())
        outer.addWidget(self._build_messages_area(), 1)
        outer.addLayout(self._build_send_row())

        self.message_input.setFocus()

    #               hlavicka

    def _build_header(self, identity: str) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel("UltraChat")
        title.setObjectName("title")
        row.addWidget(title)
        row.addStretch(1)

        self.identity = identity
        self.who = QLabel(f"prihlasen jako {identity}")
        self.who.setObjectName("muted")
        row.addWidget(self.who)
        return row

    def set_connection(self, connected: bool, queued: int) -> None:
        text = f"{self.identity} - {'online' if connected else 'offline'}"
        if queued:
            text += f" (ve fronte {queued})"
        self.who.setText(text)

    def _build_divider(self) -> QFrame:
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        return divider

    #               seznam zprav

    def _build_messages_area(self) -> QScrollArea:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        set_flat_background(self.scroll_area.viewport(), PANEL)

        content = QWidget()
        set_flat_background(content, PANEL)
        self.messages_layout = QVBoxLayout(content)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch(1)

        self.scroll_area.setWidget(content)
        bar = self.scroll_area.verticalScrollBar()
        bar.rangeChanged.connect(lambda _min, maximum: bar.setValue(maximum))
        return self.scroll_area

    def append_message(self, meta: str, text: str, variant: str) -> None:
        bubble = MessageBubble(meta, text, variant)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if variant == "own":
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)

        row_widget = QWidget()
        row_widget.setLayout(row)

        # posledni polozka layoutu je stretch, novou bublinu vlozime pred ni
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, row_widget)

    #               odesilaci radek

    def _build_send_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("prazdne = vsem")
        self.recipient_input.setFixedWidth(140)
        row.addWidget(self.recipient_input)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("napis zpravu...")
        self.message_input.returnPressed.connect(self._submit)
        row.addWidget(self.message_input, 1)

        send_button = QPushButton("Odeslat")
        send_button.setObjectName("accent")
        send_button.clicked.connect(self._submit)
        row.addWidget(send_button)

        return row

    def _submit(self) -> None:
        text = self.message_input.text().strip()
        if not text:
            return

        recipient = self.recipient_input.text().strip()
        self.on_send(recipient, text)
        self.message_input.clear()

    def set_recipient(self, identity: str) -> None:
        self.recipient_input.setText(identity)
        self.message_input.setFocus()
