"""
    Topics

    Použitá témata jsou:

    /mschat/# – celý podstrom zpráv, filtrovaný na serveru prostřednictvím ACL
    /mschat/all/# – příjem konverzací veřejného chatu.
    /mschat/all/id_odesilatele – téma, do kterého zasíláte vlastní zprávy.
    /mschat/all/anon – téma pro zasílání anonymních zpráv bez přihlášení a identity

    /mschat/status/# – stav uživatelů, kteří jej publikují. Nabývá hodnot online a offline
    /mschat/status/id_uživatele

    /mschat/user/# – obecné URL pro příjem privátních zpráv,
    /mschat/user/id_příjemce/# – URL pro příjem privátních zpráv
    /mschat/user/id_příjemce/id_odesilatele – URL pro zasílání privátních zpráv

"""

from __future__ import annotations

ROOT = "/mschat"

SUBSCRIBE_ALL = f"{ROOT}/all/#"
SUBSCRIBE_ALL_ANON = f"{ROOT}/all/anon"

def publish_to_all (id_user: str) -> str:
    """Uzel kde posílám zprávy do all chatu"""
    return f"{ROOT}/all/{id_user}"

def publish_to_all_anon():
    return f"{ROOT}/all/anon"


#       Status

SUBSCRIBE_STATUS = f"{ROOT}/status/#"

STATUS_ONLINE  = "online"
STATUS_OFFLINE = "offline"

def status_node (id_user: str) -> str:
    """Uzel stavu konkretniho uzivatele - pouzije se pro publish i pro rozpoznani pri prijmu"""
    return f"{ROOT}/status/{id_user}"


#       Privatni zpravy

def subscribe_private (id_user: str) -> str:
    """Uzel ze kterého dostávám private msg"""
    return f"{ROOT}/user/{id_user}/#"

def publish_to_private(id_reciever: str, id_sender: str) -> str:
    """Uzel kde pošlu privat msg"""
    return f"{ROOT}/user/{id_reciever}/{id_sender}"


#       Pomocna funkce pro prichozi zpravy

def parse_topic (topic: str) -> tuple[str, ...]:
    """Rozseka prijaty topic na jednotlive casti podle /"""
    return tuple(topic.split("/"))