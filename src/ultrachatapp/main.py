from ultrachatapp.connection import MQTTClient
import time


def main() -> None:
    client = MQTTClient(
        host="pcfeib425t.vsb.cz",
        port=1883,
        identity="test",
        username="mobilni",
        password="Systemy",
    )
    client.connect()

    time.sleep(2)

    client.send_public("test")

    time.sleep(5)

    client.disconnect()


if __name__ == "__main__":
    main()