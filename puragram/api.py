import json
import socket
import urllib3

from .exceptions import TelegramError, SecurityError
from .security import MAX_UPLOAD_BYTES, safe_filename
from .logger import get_logger

log = get_logger("puragram.api")


def _camel(name):
    head, *tail = name.split("_")
    return head + "".join(p.capitalize() for p in tail)


_SOCKET_OPTIONS = [
    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
]


class TelegramAPI:
    def __init__(self, token, pool_size=16, timeout=30.0,
                 connect_timeout=5.0, retries=0):
        if not token or not isinstance(token, str):
            raise SecurityError("Token must be a non-empty string")
        if ":" not in token:
            raise SecurityError("Token has invalid format")

        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.file_url = f"https://api.telegram.org/file/bot{token}"

        if retries > 0:
            retry_policy = urllib3.Retry(
                retries,
                backoff_factor=0.1,
                status_forcelist=None,
                connect=retries,
                read=0,
                redirect=0,
                raise_on_status=False,
            )
        else:
            retry_policy = False

        self._http = urllib3.PoolManager(
            num_pools=pool_size,
            maxsize=pool_size,
            block=True,
            timeout=urllib3.Timeout(
                connect=connect_timeout,
                read=timeout,
            ),
            retries=retry_policy,
            socket_options=_SOCKET_OPTIONS,
        )

    def call(self, method, files=None, **params):
        url = f"{self.base_url}/{_camel(method)}"
        try:
            if files:
                fields = self._build_multipart(files, params)
                resp = self._http.request("POST", url, fields=fields)
            else:
                body = json.dumps(
                    params, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
                resp = self._http.request(
                    "POST", url, body=body,
                    headers={"Content-Type": "application/json"},
                )
        except urllib3.exceptions.HTTPError as e:
            log.error("HTTP error calling %s: %s", method, e)
            raise TelegramError(f"HTTP error: {e}") from e

        return self._parse(resp.data)

    def stream_file(self, file_path, chunk_size=64 * 1024):
        url = f"{self.file_url}/{file_path}"
        resp = self._http.request("GET", url, preload_content=False)
        try:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            resp.release_conn()

    def close(self):
        self._http.clear()

    @staticmethod
    def _parse(raw):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise TelegramError(f"Invalid JSON from Telegram: {raw[:200]!r}")
        if not payload.get("ok"):
            raise TelegramError(
                payload.get("description", "Unknown error"),
                payload.get("error_code"),
                payload,
            )
        return payload["result"]

    @staticmethod
    def _build_multipart(files, params):
        fields = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, (dict, list)):
                fields[k] = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, bool):
                fields[k] = "true" if v else "false"
            else:
                fields[k] = str(v)

        for k, v in files.items():
            if hasattr(v, "read"):
                data = v.read()
                if isinstance(data, str):
                    data = data.encode()
                if len(data) > MAX_UPLOAD_BYTES:
                    raise SecurityError(f"File too large: {len(data)} bytes")
                name = safe_filename(getattr(v, "name", k))
                fields[k] = (name, data, "application/octet-stream")
            elif isinstance(v, (bytes, bytearray)):
                if len(v) > MAX_UPLOAD_BYTES:
                    raise SecurityError(f"File too large: {len(v)} bytes")
                fields[k] = (f"{safe_filename(k)}.bin", bytes(v),
                             "application/octet-stream")
            elif isinstance(v, str) and v.startswith("https://"):
                fields[k] = v
            elif isinstance(v, str) and v.startswith("http://"):
                raise SecurityError("Only HTTPS URLs allowed")
            else:
                raise SecurityError(
                    f"Unsupported file for {k!r}: {type(v).__name__}"
                )
        return fields
