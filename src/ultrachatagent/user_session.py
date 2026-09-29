"""
    UserSession - agent pro jednoho uzivatele

    Drzi spojeni na hlavni broker pod identitou klienta (client_id = identita)
    i kdyz je klient odpojeny. Zpravy ze serveru:
        - klient online  -> hned je prepise do jeho inboxu na lokalnim brokeru
        - klient offline -> ulozi je do fronty, po prihlaseni je vsechny posle

    Timestamp je soucasti payloadu, takze se zpravy z fronty zobrazi
    s puvodnim casem odeslani.
"""
from __future__ import annotations

import threading
from collections import deque

import paho.mqtt.client as mqtt

from ultrachatapp import topics


class UserSession:
    def __init__(self, identity: str, local: mqtt.Client,
                 host: str, port: int, username: str, password: str):
        self.identity = identity

        # spojeni na lokalni broker je spolecne pro cely agent, jen si ho pujcime
        self._local = local

        self.client_online = False
        self._queue: deque[tuple[str, bytes]] = deque()

        # paho vola callbacky z vice vlaken (upstream a lokalni spojeni),
        # zamek hlida, aby se flush fronty nepotkal s novou prichozi zpravou
        self._lock = threading.Lock()

        self._upstream = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=identity)
        self._upstream.username_pw_set(username, password)

        # kdyz spadne agent, na hlavnim brokeru se uzivatel ukaze jako offline
        self._upstream.will_set(
            topics.status_node(identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )

        self._upstream.on_connect = self._handle_connect
        self._upstream.on_message = self._handle_message

        self._upstream.connect_async(host, port, keepalive=30)
        self._upstream.loop_start()




    #               stav klienta (prichazi z lokalniho brokeru)

    def set_client_online(self, online: bool) -> None:
        with self._lock:
            self.client_online = online

            if online:
                print(f"[AGENT] {self.identity}: klient online, posilam frontu ({len(self._queue)} zprav)")
                while self._queue:
                    topic, payload = self._queue.popleft()
                    self._deliver(topic, payload)
            else:
                print(f"[AGENT] {self.identity}: klient offline, zacinam ukladat do fronty")

        # stav klienta preposleme i na hlavni broker, at ho vidi ostatni
        self._publish_status()

    def _publish_status(self) -> None:
        status = topics.STATUS_ONLINE if self.client_online else topics.STATUS_OFFLINE
        self._upstream.publish(topics.status_node(self.identity), status, qos=1, retain=True)




    #               klient -> hlavni broker

    def forward_upstream(self, topic: str, payload: bytes) -> None:
        print(f"[AGENT] {self.identity}: -> server '{topic}'")
        self._upstream.publish(topic, payload, qos=1)




    #               hlavni broker -> klient

    def _handle_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"[AGENT] {self.identity}: pripojeni na server selhalo, reason_code={reason_code}")
            return

        client.subscribe(topics.SUBSCRIBE_ALL, qos=1)
        client.subscribe(topics.SUBSCRIBE_STATUS, qos=1)
        client.subscribe(topics.subscribe_private(self.identity), qos=1)

        # po (znovu)pripojeni obnovime svuj stav - mohl ho mezitim prepsat LWT
        self._publish_status()
        print(f"[AGENT] {self.identity}: pripojeno na server")

    def _handle_message(self, client, userdata, msg):
        category = topics.parse_topic(msg.topic)[2]

        # stavy nefrontujeme - posleme je jako retained, lokalni broker si
        # posledni stav pamatuje sam a klient ho dostane hned po subscribe
        if category == "status":
            self._local.publish(topics.inbox_node(self.identity, msg.topic),
                                msg.payload, qos=1, retain=True)
            return

        with self._lock:
            if self.client_online:
                self._deliver(msg.topic, msg.payload)
            else:
                self._queue.append((msg.topic, msg.payload))
                print(f"[AGENT] {self.identity}: do fronty '{msg.topic}' (ve fronte {len(self._queue)})")

    def _deliver(self, topic: str, payload: bytes) -> None:
        self._local.publish(topics.inbox_node(self.identity, topic), payload, qos=1)




    #               ukonceni agenta

    def stop(self) -> None:
        info = self._upstream.publish(
            topics.status_node(self.identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )
        try:
            info.wait_for_publish(timeout=2)
        except (RuntimeError, ValueError):
            pass

        self._upstream.loop_stop()
        self._upstream.disconnect()
