"""Sprava pripojeni k MQTT brokeru - BrokerClient obaluje paho-mqtt."""
from __future__ import annotations

from typing import Callable, Optional

import paho.mqtt.client as mqtt

from . import topics
from .message import ChatMessage


class MQTTClient:
    def __init__(self, host: str, port: int, identity: str, username: str, password: str):
        self.host = host
        self.port = port
        self.identity = identity

        # sem si GUI napoji funkci, ktera se zavola pri prijeti zpravy
        self.on_message_received: Optional[Callable[[str, bytes], None]] = None

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=f"ultrachatapp-{identity}"        )
        self._client.username_pw_set(username, password)


        # LWT - jak padne spojeni, nastavíme offline
        self._client.will_set(
            topics.status_node(identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )

        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message




    #               pripojeni / odpojeni

    def connect(self) -> None:
        self._client.connect(self.host, self.port, keepalive=30)
        self._client.loop_start()

    def disconnect(self) -> None:
        # korektni odhlaseni - rucne posleme "offline" (retained)
        self._client.publish(
            topics.status_node(self.identity),
            payload=topics.STATUS_OFFLINE,
            qos=1,
            retain=True,
        )
        self._client.loop_stop()
        self._client.disconnect()




    #               interni handlery

    def _handle_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"Pripojeni selhalo, reason_code={reason_code}")
            return

        # all chat, stav vsech uzivatelu a mych private msgs
        client.subscribe(topics.SUBSCRIBE_ALL, qos=1)
        client.subscribe(topics.SUBSCRIBE_STATUS, qos=1)
        client.subscribe(topics.subscribe_private(self.identity), qos=1)

        # pošlem že jsem online
        client.publish(
            topics.status_node(self.identity),
            payload=topics.STATUS_ONLINE,
            qos=1,
            retain=True,
        )
        print(" Připojeno k serveru :)")

    def _handle_message(self, client, userdata, msg):
        if self.on_message_received:
            self.on_message_received(msg.topic, msg.payload)



    #              odeslání msg

    def send_public(self, text: str) -> None:
        payload = ChatMessage.new(text).encode()
        self._client.publish(topics.publish_to_all(self.identity), payload, qos=1)

    def send_private(self, recipient: str, text: str) -> None:
        payload = ChatMessage.new(text).encode()
        self._client.publish(
            topics.publish_to_private(recipient, self.identity), payload, qos=1
        )