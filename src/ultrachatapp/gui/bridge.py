"""Prevod MQTT callbacku (bezi ve vlakne paho) do Qt hlavniho vlakna pres signal."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class MqttBridge(QObject):
    message_received = pyqtSignal(str, bytes)
    connection_changed = pyqtSignal(bool, int)
