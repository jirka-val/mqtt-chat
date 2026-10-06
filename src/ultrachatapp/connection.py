"""Sprava pripojeni k MQTT brokeru - BrokerClient obaluje paho-mqtt."""
from __future__ import annotations

import threading
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from . import topics
from .message import ChatMessage
from .outbox import Outbox

# jak casto si znovu nechame poslat stavy vsech uzivatelu (s)
STATUS_REFRESH_INTERVAL = 30

# po jak dlouhe dobe bez spojeni rekneme GUI, ze jsou vsichni offline (s)
OFFLINE_TIMEOUT = 15


class MQTTClient:
    def __init__(self, host: str, port: int, identity: str, username: str, password: str,
                 via_agent: bool = False):
        self.host = host
        self.port = port
        self.identity = identity

        # pres agenta (cviko 2) - pripojujeme se na lokalni mosquitto a zpravy
        # cteme jen ze sveho inboxu, kam je agent preposila z hlavniho brokeru
        self.via_agent = via_agent

        # sem si GUI napoji funkci, ktera se zavola pri prijeti zpravy
        self.on_message_received: Optional[Callable[[str, bytes], None]] = None

        # a sem funkci pro zmenu stavu spojeni (pripojeno, pocet zprav ve fronte)
        self.on_connection_changed: Optional[Callable[[bool, int], None]] = None

        # offline rezim (cviko 3)
        self.connected = False
        self.statuses: dict[str, str] = {}
        self.outbox = Outbox()
        self._closing = False
        self._offline_timer: threading.Timer | None = None
        self._refresh_timer: threading.Timer | None = None

        # client_id musi byt shodne s identitou - ACL na serveru pravdepodobne
        # povoluje zapis jen na topic odpovidajici client_id (%c v mosquitto ACL)
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=identity)
        self._client.username_pw_set(username, password)

        # po vypadku se paho pripojuje samo, zkousi to kazdych 1-5 s
        self._client.reconnect_delay_set(min_delay=1, max_delay=5)


        # LWT - jak padne spojeni, nastavíme offline
        self._client.will_set(
            topics.status_node(identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )

        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._client.on_message = self._handle_message
        self._client.on_publish = self._handle_publish




    #               pripojeni / odpojeni

    def connect(self) -> None:
        # keepalive 10 s, at se vypadek pozna rychle (broker i my to poznaji az po 1.5x keepalive)
        self._client.connect(self.host, self.port, keepalive=10)
        self._client.loop_start()
        self._schedule_status_refresh()

    def disconnect(self) -> None:
        self._closing = True
        self._cancel_timers()

        # korektni odhlaseni - rucne posleme "offline" (retained) a pockame,
        # az se opravdu odesle - jinak muze loop_stop() vlakno zastavit driv,
        # nez publish stihne odejit, a offline status se nikdy nedoruci
        info = self._client.publish(
            topics.status_node(self.identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )
        try:
            info.wait_for_publish(timeout=2)
        except (RuntimeError, ValueError):
            pass

        self._client.loop_stop()
        self._client.disconnect()




    #               interni handlery

    def _handle_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"Pripojeni selhalo, reason_code={reason_code}")
            return

        if self.via_agent:
            # agent nam posila vsechno (all, status, private) do jednoho inboxu
            client.subscribe(topics.subscribe_inbox(self.identity), qos=1)
            print(f"[DEBUG] {self.identity}: subscribed na {topics.subscribe_inbox(self.identity)}")
        else:
            # all chat, stav vsech uzivatelu a mych private msgs
            client.subscribe(topics.SUBSCRIBE_ALL, qos=1)
            client.subscribe(topics.SUBSCRIBE_STATUS, qos=1)
            client.subscribe(topics.subscribe_private(self.identity), qos=1)
            print(f"[DEBUG] {self.identity}: subscribed na {topics.SUBSCRIBE_ALL}, "
                  f"{topics.SUBSCRIBE_STATUS}, {topics.subscribe_private(self.identity)}")

        # pošlem že jsem online
        client.publish(
            topics.status_node(self.identity),
            payload=topics.STATUS_ONLINE,
            qos=1,
            retain=True,
        )
        print(" Připojeno k serveru :)")

        self.connected = True
        if self._offline_timer is not None:
            self._offline_timer.cancel()
            self._offline_timer = None

        # stare stavy zahodime, server nam po subscribe hned posle aktualni (retained)
        # soukrome zpravy z fronty tak odejdou az podle opravdoveho stavu prijemce
        self.statuses.clear()
        self._flush_outbox()

    def _handle_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = False
        if self._closing:
            return

        print(f"[DEBUG] {self.identity}: spojeni ztraceno rc={reason_code}, zpravy jdou do fronty")
        self._notify_connection()

        # kdyz se do OFFLINE_TIMEOUT nepripojime, vsichni budou v GUI offline
        if self._offline_timer is None:
            self._offline_timer = threading.Timer(OFFLINE_TIMEOUT, self._mark_all_offline)
            self._offline_timer.daemon = True
            self._offline_timer.start()

    def _handle_message(self, client, userdata, msg):
        print(f"[DEBUG] {self.identity}: prijato na '{msg.topic}' -> {msg.payload!r}")

        # z /inbox/ja/mschat/all/pepa udelame zpet /mschat/all/pepa,
        # GUI pak nepozna rozdil, jestli jedeme pres agenta nebo primo
        topic = msg.topic
        if self.via_agent:
            topic = topics.strip_inbox(self.identity, topic)

        parts = topics.parse_topic(topic)
        if parts[2] == "status":
            status = msg.payload.decode("utf-8", errors="replace")
            self.statuses[parts[3]] = status

            # nekdo se pripojil - treba pro nej mame soukrome zpravy ve fronte
            if status == topics.STATUS_ONLINE:
                self._flush_outbox()

        if self.on_message_received:
            self.on_message_received(topic, msg.payload)

    def _handle_publish(self, client, userdata, mid, reason_code=None, properties=None):
        print(f"[DEBUG] {self.identity}: broker potvrdil publish mid={mid} rc={reason_code}")



    #              odeslání msg

    def send_public(self, text: str) -> None:
        payload = ChatMessage.new(text).encode()
        self._send(topics.publish_to_all(self.identity), payload)

    def send_private(self, recipient: str, text: str) -> None:
        payload = ChatMessage.new(text).encode()
        self._send(topics.publish_to_private(recipient, self.identity), payload, recipient)

    def _send(self, topic: str, payload: bytes, recipient: str = "") -> None:
        if not self.connected:
            self.outbox.add(topic, payload, recipient)
            print(f"[DEBUG] {self.identity}: offline, '{topic}' do fronty (ve fronte {len(self.outbox)})")
            self._notify_connection()
            return

        info = self._client.publish(topic, payload, qos=1)
        print(f"[DEBUG] {self.identity}: publish na '{topic}' rc={info.rc} mid={info.mid}")




    #               offline rezim (cviko 3)

    def _flush_outbox(self) -> None:
        if not self.connected:
            return

        for topic, payload in self.outbox.take_ready(self._is_online):
            info = self._client.publish(topic, payload, qos=1)
            print(f"[DEBUG] {self.identity}: z fronty na '{topic}' rc={info.rc} mid={info.mid}")

        self._notify_connection()

    def _is_online(self, identity: str) -> bool:
        return self.statuses.get(identity) == topics.STATUS_ONLINE

    def _mark_all_offline(self) -> None:
        if self.connected:
            return

        # self.statuses nemenime, je to posledni znamy seznam
        # spravne stavy prijdou od serveru po znovupripojeni
        print(f"[DEBUG] {self.identity}: server porad nedostupny, vsichni offline")
        if self.on_message_received:
            for identity in list(self.statuses):
                self.on_message_received(topics.status_node(identity), topics.STATUS_OFFLINE.encode())

    def _schedule_status_refresh(self) -> None:
        self._refresh_timer = threading.Timer(STATUS_REFRESH_INTERVAL, self._refresh_statuses)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

    def _refresh_statuses(self) -> None:
        # opakovany subscribe = broker znovu posle vsechny retained zpravy, tj. stavy uzivatelu
        if self.connected:
            topic = topics.subscribe_inbox(self.identity) if self.via_agent else topics.SUBSCRIBE_STATUS
            self._client.subscribe(topic, qos=1)
            print(f"[DEBUG] {self.identity}: obnovuji seznam uzivatelu")

        if not self._closing:
            self._schedule_status_refresh()

    def _notify_connection(self) -> None:
        if self.on_connection_changed:
            self.on_connection_changed(self.connected, len(self.outbox))

    def _cancel_timers(self) -> None:
        for timer in (self._offline_timer, self._refresh_timer):
            if timer is not None:
                timer.cancel()
