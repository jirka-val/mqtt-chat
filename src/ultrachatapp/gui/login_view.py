"""Prihlasovaci obrazovka. Jen sbira udaje, o MQTT nic nevi."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import apply_card_shadow


@dataclass
class LoginData:
    host: str
    port: int
    identity: str
    username: str
    password: str
    via_agent: bool


class LoginView(QWidget):
    def __init__(self, defaults: dict, on_submit: Callable[[LoginData], None]):
        super().__init__()
        self.on_submit = on_submit
        self.defaults = defaults

        outer = QVBoxLayout(self)
        outer.addStretch(1)

        center_row = QHBoxLayout()
        center_row.addStretch(1)
        center_row.addWidget(self._build_card(defaults))
        center_row.addStretch(1)
        outer.addLayout(center_row)

        outer.addStretch(1)

    def _build_card(self, defaults: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(340)
        apply_card_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(10)

        title = QLabel("UltraChat")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(14)

        self.host_input = self._field(layout, "Host", defaults.get("host", ""))
        self.port_input = self._field(layout, "Port", str(defaults.get("port", "")))
        self.identity_input = self._field(layout, "Identita (login)", "")
        self.username_input = self._field(layout, "MQTT uzivatel", defaults.get("username", ""))
        self.password_input = self._field(
            layout, "MQTT heslo", defaults.get("password", ""), secret=True
        )

        # cviko 2 - pripojeni pres agenta na lokalnim mosquittu
        self.agent_checkbox = QCheckBox("Pres agenta")
        self.agent_checkbox.toggled.connect(self._toggle_agent)
        layout.addWidget(self.agent_checkbox)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        connect_button = QPushButton("Pripojit")
        connect_button.setObjectName("accent")
        connect_button.clicked.connect(self._submit)
        layout.addWidget(connect_button)

        self.identity_input.setFocus()
        for field in (
            self.host_input,
            self.port_input,
            self.identity_input,
            self.username_input,
            self.password_input,
        ):
            field.returnPressed.connect(self._submit)

        return card

    def _field(self, layout: QVBoxLayout, label: str, default: str, secret: bool = False) -> QLineEdit:
        field_label = QLabel(label)
        field_label.setObjectName("fieldLabel")
        layout.addWidget(field_label)

        entry = QLineEdit(default)
        if secret:
            entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(entry)
        return entry

    def _toggle_agent(self, checked: bool) -> None:
        """Prepne host/port mezi hlavnim brokerem a lokalnim agentem.
        U agenta je login zaroven identita (ACL na nem stoji), tak ho predvyplnime."""
        if checked:
            self.host_input.setText(self.defaults.get("agent_host", ""))
            self.port_input.setText(str(self.defaults.get("agent_port", "")))
            self.username_input.setText(self.identity_input.text().strip())
            self.password_input.clear()
        else:
            self.host_input.setText(self.defaults.get("host", ""))
            self.port_input.setText(str(self.defaults.get("port", "")))
            self.username_input.setText(self.defaults.get("username", ""))
            self.password_input.setText(self.defaults.get("password", ""))

    def show_error(self, text: str) -> None:
        self.error_label.setText(text)

    def _submit(self) -> None:
        identity = self.identity_input.text().strip()
        if not identity:
            self.show_error("Zadej identitu")
            return

        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            self.show_error("Port musi byt cislo")
            return

        self.on_submit(
            LoginData(
                host=self.host_input.text().strip(),
                port=port,
                identity=identity,
                username=self.username_input.text().strip(),
                password=self.password_input.text(),
                via_agent=self.agent_checkbox.isChecked(),
            )
        )
