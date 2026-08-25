"""API interna mínima para ejecutar dbt sin exponer el socket Docker a NiFi."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
from threading import Lock
from urllib.parse import parse_qs, urlparse


_DBT_LOCK = Lock()


class DbtRequestHandler(BaseHTTPRequestHandler):
    server_version = "TFMdbt/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print(json.dumps({"event": "dbt_http", "message": format % args}))

    def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "service": "dbt"})
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/run":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        if not _DBT_LOCK.acquire(blocking=False):
            self._send(HTTPStatus.CONFLICT, {"error": "dbt_in_progress"})
            return
        try:
            query = parse_qs(parsed.query)
            command = [
                "dbt",
                "build",
                "--project-dir",
                "/usr/app",
                "--profiles-dir",
                "/usr/app",
            ]
            selection = query.get("select", [""])[0].strip()
            if selection:
                command.extend(["--select", selection])
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            payload = {
                "event": "dbt_build_complete" if result.returncode == 0 else "dbt_build_failed",
                "return_code": result.returncode,
                "stdout_tail": result.stdout[-12000:],
                "stderr_tail": result.stderr[-4000:],
            }
            self._send(
                HTTPStatus.OK if result.returncode == 0 else HTTPStatus.INTERNAL_SERVER_ERROR,
                payload,
            )
        except subprocess.TimeoutExpired:
            self._send(HTTPStatus.GATEWAY_TIMEOUT, {"error": "dbt_timeout"})
        finally:
            _DBT_LOCK.release()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), DbtRequestHandler)
    print(json.dumps({"event": "dbt_service_ready", "port": 8080}))
    server.serve_forever()
