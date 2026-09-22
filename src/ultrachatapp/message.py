"""

    Format zprávy by měl vypadat

    POSIX timestamp + msg

"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ChatMessage:
    timestamp: float
    text: str


    @classmethod
    def new(cls, text: str) -> "ChatMessage":
        """Vytvori novou msg s aktualnim casem """
        return cls(timestamp=time.time(), text=text)

    def encode(self) -> bytes:
        """ Zakodujem naši zpravu do formatu ,,timestamp text´´ """
        return f"{self.timestamp} {self.text}".encode("utf-8")

    @classmethod
    def decode(cls, payload: bytes) -> "ChatMessage":
        """
        pokusíme se to rozkodovat
        Nevěřím nikomu. beztak to tam někdo dal s /n
        """
        raw = payload.decode("utf-8", errors="replace")

        if " " in raw:
            ts_part, text_part = raw.split(" ", 1)
        elif "\n" in raw:
            ts_part, text_part = raw.split("\n", 1)
        else:
            ts_part, text_part = "", raw

        try:
            ts = float(ts_part.strip())
        except ValueError:
            # rlly? bez timestampu... gg
            ts = time.time()
            text_part = raw

        return cls(timestamp=ts, text=text_part)