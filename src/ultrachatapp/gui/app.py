"""Hlavni okno - prepina login/chat obrazovku a propojuje je s MQTTClient."""
from __future__ import annotations

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from .. import topics
from ..connection import MQTTClient
from ..message import ChatMessage
from .bridge import MqttBridge
from .chat_view import ChatView
from .login_view import LoginData, LoginView
from .theme import STYLESHEET
from .user_list_view import UserListView

load_dotenv()

DEFAULT_HOST = "pcfeib425t.vsb.cz"
DEFAULT_PORT = 1883

# lokalni mosquitto, u ktereho bezi agent (cviko 2)
AGENT_HOST = "localhost"
AGENT_PORT = 1884


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UltraChat")
        self.resize(900, 620)
        self.setMinimumSize(640, 440)

        self.client: MQTTClient | None = None
        self.identity: str = ""
        self.chat_view: ChatView | None = None
        self.user_list: UserListView | None = None

        self.bridge = MqttBridge()
        self.bridge.message_received.connect(self._handle_message)
        self.bridge.connection_changed.connect(self._handle_connection)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_login_screen()

    #               prepinani obrazovek

    def _build_login_screen(self) -> None:
        defaults = {
            "host": DEFAULT_HOST,
            "port": DEFAULT_PORT,
            "username": os.getenv("MQTT_USERNAME", ""),
            "password": os.getenv("MQTT_PASSWORD", ""),
            "agent_host": AGENT_HOST,
            "agent_port": AGENT_PORT,
        }
        self.login_view = LoginView(defaults, self._on_login)
        self.stack.addWidget(self.login_view)
        self.stack.setCurrentWidget(self.login_view)

    def _build_chat_screen(self, identity: str) -> None:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        self.chat_view = ChatView(identity, self._on_send)
        self.user_list = UserListView()
        self.user_list.user_selected.connect(self.chat_view.set_recipient)

        layout.addWidget(self.chat_view, 1)
        layout.addWidget(self.user_list, 0)

        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    #               prihlaseni

    def _on_login(self, data: LoginData) -> None:
        client = MQTTClient(
            host=data.host,
            port=data.port,
            identity=data.identity,
            username=data.username,
            password=data.password,
            via_agent=data.via_agent,
        )
        client.on_message_received = self._on_mqtt_message
        client.on_connection_changed = self.bridge.connection_changed.emit

        try:
            client.connect()
        except Exception as exc:
            self.login_view.show_error(f"Pripojeni selhalo: {exc}")
            return

        self.client = client
        self.identity = data.identity
        self._build_chat_screen(data.identity)

    #               odesilani zprav (moje zpravy se rovnou zobrazi lokalne,
    #               broker je odesilateli zpatky neposila)

    def _on_send(self, recipient: str, text: str) -> None:
        if self.client is None or self.chat_view is None:
            return

        time_str = datetime.now().strftime("%H:%M")
        if recipient:
            self.client.send_private(recipient, text)
            self.chat_view.append_message(f"Ty -> {recipient} - {time_str}", text, "own")
        else:
            self.client.send_public(text)
            self.chat_view.append_message(f"Ty - {time_str}", text, "own")

    #               prijem zprav

    def _on_mqtt_message(self, topic: str, payload: bytes) -> None:
        # bezi ve vlakne paho, signal to bezpecne preda do hlavniho Qt vlakna
        self.bridge.message_received.emit(topic, payload)

    def _handle_message(self, topic: str, payload: bytes) -> None:
        # topic zacina "/", takze parts[0] je prazdny retezec, parts[1] je "mschat"
        parts = topics.parse_topic(topic)
        category = parts[2]

        if category == "status" and self.user_list is not None:
            self.user_list.set_status(parts[3], payload.decode("utf-8", errors="replace"))
            return

        if self.chat_view is None:
            return

        msg = ChatMessage.decode(payload)
        time_str = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M")

        if category == "all":
            sender = parts[3]
            if sender == self.identity:
                return
            self.chat_view.append_message(f"{sender} - {time_str}", msg.text, "all")
        elif category == "user":
            sender = parts[4]
            if sender == self.identity:
                return
            self.chat_view.append_message(
                f"{sender} (soukrome) - {time_str}", msg.text, "private"
            )

    def _handle_connection(self, connected: bool, queued: int) -> None:
        if self.chat_view is not None:
            self.chat_view.set_connection(connected, queued)

    def closeEvent(self, event) -> None:
        if self.client is not None:
            self.client.disconnect()
        super().closeEvent(event)


def run() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
