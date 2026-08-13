"""API HTTP interna para salud y activación controlada del entrenamiento."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Lock
from urllib.parse import parse_qs, urlparse

from nyc_taxi_ml.config import load_config
from nyc_taxi_ml.modeling import train_demand_models


_TRAINING_LOCK = Lock()


class MlRequestHandler(BaseHTTPRequestHandler):
    server_version = "TFMML/0.3"

    def log_message(self, format: str, *args: object) -> None:
        print(json.dumps({"event": "ml_http", "message": format % args}))

    def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "service": "ml"})
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/train":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        mode = parse_qs(parsed.query).get("mode", ["demo"])[0]
        if mode not in {"demo", "full"}:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_mode"})
            return
        if not _TRAINING_LOCK.acquire(blocking=False):
            self._send(HTTPStatus.CONFLICT, {"error": "training_in_progress"})
            return
        try:
            self._send(HTTPStatus.OK, train_demand_models(load_config(), mode))
        except Exception as exc:
            self._send(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": type(exc).__name__, "message": str(exc)},
            )
        finally:
            _TRAINING_LOCK.release()


def serve(host: str = "0.0.0.0", port: int = 8081) -> None:
    server = ThreadingHTTPServer((host, port), MlRequestHandler)
    print(json.dumps({"event": "ml_service_ready", "host": host, "port": port}))
    server.serve_forever()
