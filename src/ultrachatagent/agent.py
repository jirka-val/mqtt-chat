"""
    Agent - proxy mezi lokalnim mosquittem (kam se pripojuji klienti)
    a hlavnim brokerem (pcfeib425t.vsb.cz)

    Na lokalni broker se agent prihlasi jednim spojenim jako superuser
    a posloucha, co klienti publikuji. Pro kazdeho klienta si vytvori
    UserSession, ktera drzi jeho vlastni spojeni na hlavni broker.

    Klienti jsou na lokalnim brokeru overeni pres mosquitto_passwd a ACL
    jim dovoli zapisovat jen do svych topicu - diky tomu muze agent
    identitu odesilatele bezpecne precist primo z topicu.
"""
from __future__ import annotations

import threading

import paho.mqtt.client as mqtt

from ultrachatapp import topics
from .user_session import UserSession


class Agent:
    def __init__(self, local_host: str, local_port: int, local_username: str, local_password: str,
                 upstream_host: str, upstream_port: int, upstream_username: str, upstream_password: str):
        self.local_host = local_host
        self.local_port = local_port

        # udaje pro hlavni broker, kazda UserSession je pouzije pro sve spojeni
        self._upstream_config = (upstream_host, upstream_port, upstream_username, upstream_password)

        self.sessions: dict[str, UserSession] = {}
        self._sessions_lock = threading.Lock()

        self._local = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ultrachat-agent")
        self._local.username_pw_set(local_username, local_password)
        self._local.on_connect = self._handle_connect
        self._local.on_message = self._handle_message




    #               pripojeni / odpojeni

    def start(self) -> None:
        self._local.connect(self.local_host, self.local_port, keepalive=30)
        self._local.loop_start()

    def stop(self) -> None:
        with self._sessions_lock:
            for session in self.sessions.values():
                session.stop()

        self._local.loop_stop()
        self._local.disconnect()




    #               sessions

    def _get_session(self, identity: str) -> UserSession:
        """Vrati session uzivatele, pri prvnim kontaktu ji zalozi (a pripoji na server)"""
        with self._sessions_lock:
            if identity not in self.sessions:
                print(f"[AGENT] nova session pro '{identity}'")
                host, port, username, password = self._upstream_config
                self.sessions[identity] = UserSession(
                    identity, self._local, host, port, username, password
                )
            return self.sessions[identity]




    #               lokalni broker (klienti -> agent)

    def _handle_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"[AGENT] pripojeni na lokalni broker selhalo, reason_code={reason_code}")
            return

        # jen topicy, kam klienti PISOU - ACL zaruci, ze kazdy jen do svych
        client.subscribe(f"{topics.ROOT}/all/+", qos=1)
        client.subscribe(f"{topics.ROOT}/user/+/+", qos=1)
        client.subscribe(f"{topics.ROOT}/status/+", qos=1)
        print(f"[AGENT] pripojeno na lokalni broker {self.local_host}:{self.local_port}")

    def _handle_message(self, client, userdata, msg):
        # topic zacina "/", takze parts[0] je prazdny retezec, parts[1] je "mschat"
        parts = topics.parse_topic(msg.topic)
        category = parts[2]

        if category == "status":
            # klient se pripojil (online) / odpojil nebo spadl (offline - LWT)
            # retained stavy prijdou i po restartu agenta -> session se obnovi
            online = msg.payload.decode("utf-8", errors="replace") == topics.STATUS_ONLINE
            self._get_session(parts[3]).set_client_online(online)

        elif category == "all":
            self._get_session(parts[3]).forward_upstream(msg.topic, msg.payload)

        elif category == "user":
            self._get_session(parts[4]).forward_upstream(msg.topic, msg.payload)
