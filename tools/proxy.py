"""
    TCP proxy na simulaci vypadku spojeni (test cviko 3)

    Klient se pripoji na localhost:1885 misto primo na server,
    proxy vsechno preposila dal na server a zpatky

        Ctrl+C          -> proxy skonci, klientovi spadne spojeni = vypadek
        znovu spustit   -> klient se sam pripoji = spojeni obnoveno

    Spusteni:  .venv\\Scripts\\python.exe tools/proxy.py [host] [port]
"""
import socket
import sys
import threading

LISTEN_PORT = 1885

target_host = sys.argv[1] if len(sys.argv) > 1 else "pcfeib425t.vsb.cz"
target_port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883


def pipe(src: socket.socket, dst: socket.socket) -> None:
    """Preposila data jednim smerem, dokud se jedna strana neodpoji"""
    try:
        while data := src.recv(4096):
            dst.sendall(data)
    except OSError:
        pass
    finally:
        src.close()
        dst.close()


def run() -> None:
    server = socket.socket()
    server.bind(("localhost", LISTEN_PORT))
    server.listen()

    # na Windows by accept() bez timeoutu nereagoval na Ctrl+C
    server.settimeout(1)
    print(f"[PROXY] localhost:{LISTEN_PORT} -> {target_host}:{target_port}, vypadek = Ctrl+C")

    while True:
        try:
            client, addr = server.accept()
        except socket.timeout:
            continue

        client.settimeout(None)
        try:
            upstream = socket.create_connection((target_host, target_port), timeout=5)
            upstream.settimeout(None)
        except OSError as exc:
            print(f"[PROXY] server nedostupny: {exc}")
            client.close()
            continue

        print(f"[PROXY] nove spojeni z {addr[0]}:{addr[1]}")
        threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
        threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("[PROXY] konec - spojeni prerusena")
