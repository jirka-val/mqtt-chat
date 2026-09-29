"""Vstupni bod agenta - nacte .env, spusti agenta a bezi, dokud ho neukoncis Ctrl+C."""
from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from ultrachatagent.agent import Agent

load_dotenv()


def run() -> None:
    agent = Agent(
        local_host=os.getenv("AGENT_LOCAL_HOST", "localhost"),
        local_port=int(os.getenv("AGENT_LOCAL_PORT", "1884")),
        local_username=os.getenv("AGENT_LOCAL_USERNAME", "VAL0475-agent"),
        local_password=os.getenv("AGENT_LOCAL_PASSWORD", ""),
        upstream_host=os.getenv("AGENT_UPSTREAM_HOST", "pcfeib425t.vsb.cz"),
        upstream_port=int(os.getenv("AGENT_UPSTREAM_PORT", "1883")),
        upstream_username=os.getenv("AGENT_UPSTREAM_USERNAME", "server"),
        upstream_password=os.getenv("AGENT_UPSTREAM_PASSWORD", "Broker"),
    )
    agent.start()
    print("[AGENT] bezim, ukonceni Ctrl+C")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[AGENT] koncim")
        agent.stop()


if __name__ == "__main__":
    run()
