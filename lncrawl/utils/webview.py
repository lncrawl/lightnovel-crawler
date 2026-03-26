import logging
import socket
import threading
import time

import webview

from ..commands.server import server
from ..context import ctx
from ..dao.enums import UserRole

logger = logging.getLogger(__name__)


def start_webview() -> None:
    host = "127.0.0.1"
    port = 8080

    t = threading.Thread(
        target=server,
        kwargs={
            "host": host,
            "port": port,
        },
        daemon=True,
        name="server",
    )
    t.start()

    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.05)
    else:
        logger.error(f"Server failed to start on {host}:{port}")
        raise SystemExit(1)

    token = ctx.users.generate_token(
        user=ctx.users.get_admin(),
        expiry_minutes=100 * 365 * 24 * 60,  # 100 years
        scopes=[UserRole.LOCAL],
    )
    webview.create_window(
        "Lightnovel Crawler",
        f"http://{host}:{port}/?authToken={token}",
        maximized=True,
        width=1200,
        height=850,
    )
    webview.start()
