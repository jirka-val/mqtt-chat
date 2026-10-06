"""
    Outbox - fronta zprav napsanych v offline rezimu

    Payload se vytvori uz pri napsani zpravy, takze v nem zustane
    puvodni timestamp a prijemce uvidi cas, kdy byla zprava napsana

    Soukrome zpravy pro uzivatele, ktery je zrovna offline, ve fronte
    pockaji, dokud se znovu nepripoji
"""
from __future__ import annotations

import threading
from typing import Callable


class Outbox:
    def __init__(self):
        # (topic, payload, prijemce) - u verejnych zprav je prijemce ""
        self._messages: list[tuple[str, bytes, str]] = []

        # pridava GUI vlakno, vybira vlakno paho
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._messages)

    def add(self, topic: str, payload: bytes, recipient: str = "") -> None:
        with self._lock:
            self._messages.append((topic, payload, recipient))

    def take_ready(self, is_online: Callable[[str], bool]) -> list[tuple[str, bytes]]:
        """Vynda zpravy, co muzou odejit - verejne vzdy, soukrome jen kdyz je prijemce online"""
        ready = []
        waiting = []

        with self._lock:
            for topic, payload, recipient in self._messages:
                if recipient and not is_online(recipient):
                    waiting.append((topic, payload, recipient))
                else:
                    ready.append((topic, payload))
            self._messages = waiting

        return ready
