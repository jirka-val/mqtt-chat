"""Jedna bublina zpravy v chatu."""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

VARIANT_OBJECT_NAMES = {
    "own": "bubbleOwn",
    "all": "bubbleAll",
    "private": "bubblePrivate",
}

MAX_BUBBLE_WIDTH = 380


class MessageBubble(QFrame):
    def __init__(self, meta: str, text: str, variant: str):
        super().__init__()
        self.setObjectName(VARIANT_OBJECT_NAMES.get(variant, "bubbleAll"))
        self.setMaximumWidth(MAX_BUBBLE_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 9)
        layout.setSpacing(2)

        meta_label = QLabel(meta)
        meta_label.setObjectName("bubbleMeta")
        layout.addWidget(meta_label)

        body_label = QLabel(text)
        body_label.setObjectName("bubbleBody")
        body_label.setWordWrap(True)
        layout.addWidget(body_label)
