"""Serveur HTTP read-only base sur ThreadingHTTPServer."""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from ..app import App
from .handlers import build_router
from .router import HttpError, Router


def make_handler(router: Router):
    class Handler(BaseHTTPRequestHandler):
        server_version = "mmi-kb/0.1"

        def _respond(self, method: str) -> None:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query, keep_blank_values=False)
            try:
                response = router.dispatch(method, parsed.path, query)
            except HttpError as exc:
                response = self._error(exc.status, exc.message)
            except Exception as exc:  # pragma: no cover - garde-fou serveur
                print(f"mmi-kb: erreur interne : {exc}", file=sys.stderr)
                response = self._error(500, "erreur interne")
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.send_header("Cache-Control", "no-store")
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(response.body)

        @staticmethod
        def _error(status: int, message: str):
            from .router import Response
            return Response.json({"error": message}, status=status)

        def do_GET(self) -> None:  # noqa: N802
            self._respond("GET")

        def do_HEAD(self) -> None:  # noqa: N802
            self._respond("HEAD")

        def log_message(self, fmt: str, *args) -> None:
            print(f"mmi-kb: {self.address_string()} - {fmt % args}", file=sys.stderr)

    return Handler


def serve(app: App, host: str = "127.0.0.1", port: int = 8091) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(build_router(app)))
    print(f"mmi-kb: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
