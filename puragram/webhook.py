import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .logger import get_logger
from .security import MAX_WEBHOOK_BYTES, constant_time_eq
from .types import Update

log = get_logger("puragram.webhook")


class WebhookServer:
    def __init__(self, bot, host="127.0.0.1", port=8080, path="/webhook",
                 secret_token=None, max_bytes=MAX_WEBHOOK_BYTES):
        if secret_token is not None and len(secret_token) < 16:
            raise ValueError("secret_token must be at least 16 chars")
        self.bot = bot
        self.host = host
        self.port = port
        self.path = path
        self.secret_token = secret_token
        self.max_bytes = max_bytes
        self._server = None
        self._thread = None

    def _make_handler(self):
        bot = self.bot
        expected_path = self.path
        secret = self.secret_token
        max_bytes = self.max_bytes

        class Handler(BaseHTTPRequestHandler):
            server_version = "puragram"
            sys_version = ""

            def do_POST(self):
                if self.path != expected_path:
                    self._reply(404, {"ok": False, "error": "not found"})
                    return

                if secret:
                    got = self.headers.get(
                        "X-Telegram-Bot-Api-Secret-Token", ""
                    )
                    if not constant_time_eq(got, secret):
                        log.warning("webhook forbidden from %s",
                                    self.client_address[0])
                        self._reply(403, {"ok": False, "error": "forbidden"})
                        return

                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._reply(400, {"ok": False, "error": "bad length"})
                    return

                if length <= 0 or length > max_bytes:
                    self._reply(413, {"ok": False, "error": "payload too large"})
                    return

                raw = self.rfile.read(length)
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    self._reply(400, {"ok": False, "error": "bad json"})
                    return

                if not isinstance(data, dict) or "update_id" not in data:
                    self._reply(400, {"ok": False, "error": "bad update"})
                    return

                try:
                    bot._dispatch(Update.from_dict(data))
                except Exception:
                    log.exception("webhook dispatch failed")
                    self._reply(500, {"ok": False})
                    return

                self._reply(200, {"ok": True})

            def do_GET(self):
                if self.path == "/health":
                    self._reply(200, {"ok": True, "bot": "puragram"})
                else:
                    self._reply(404, {"ok": False})

            def _reply(self, code, payload):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                log.debug("webhook %s", args[0] if args else "")

        return Handler

    def start(self, blocking=True):
        self._server = ThreadingHTTPServer(
            (self.host, self.port), self._make_handler()
        )
        log.info("webhook server on %s:%s%s",
                 self.host, self.port, self.path)
        if blocking:
            self._server.serve_forever()
        else:
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def install(self, public_url):
        if not public_url.startswith("https://"):
            raise ValueError("Webhook URL must be HTTPS")
        return self.bot.set_webhook(
            url=public_url,
            secret_token=self.secret_token,
            allowed_updates=self.bot._collect_allowed_updates(),
        )