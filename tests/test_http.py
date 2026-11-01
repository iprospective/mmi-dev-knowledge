#!/usr/bin/env python3
"""Tests du router et du serveur HTTP read-only."""
import json
import pathlib
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmi_kb.app import App  # noqa: E402
from mmi_kb.http.handlers import build_router  # noqa: E402
from mmi_kb.http.router import HttpError  # noqa: E402
from mmi_kb.http.server import make_handler  # noqa: E402

failures = 0


def check(label, cond):
    global failures
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond:
        failures += 1


def main():
    router = build_router(App(ROOT))

    check("GET /", router.dispatch("GET", "/", {}).status == 200)
    health = json.loads(router.dispatch("GET", "/health", {}).body)
    check("health", health.get("status") == "ok" and health.get("knowledge_commit"))
    compat = json.loads(router.dispatch("GET", "/views/compat", {"php": ["8.1"]}).body)
    check("vue compat", compat.get("view") == "compat" and compat.get("filters") == {"php": "8.1"})
    entity = json.loads(router.dispatch("GET", "/entities/tool:dolibarr", {}).body)
    check("fiche outil", entity.get("id") == "tool:dolibarr")
    entity = json.loads(router.dispatch("GET", "/entities/quirk:dolibarr/pdf-sponge-round-string", {}).body)
    check("fiche avec slash", entity.get("id") == "quirk:dolibarr/pdf-sponge-round-string")

    for path in ("/inconnue", "/entities/absent"):
        try:
            router.dispatch("GET", path, {})
        except HttpError as exc:
            check(f"{path} -> 404", exc.status == 404)
        else:
            check(f"{path} -> 404", False)

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(router))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(base + "/health", timeout=5) as response:
            payload = json.loads(response.read())
            check("serveur health", response.status == 200 and payload["status"] == "ok")
        with urllib.request.urlopen(base + "/views/tests", timeout=5) as response:
            check("serveur vue", json.loads(response.read())["view"] == "tests")
        try:
            urllib.request.urlopen(base + "/inconnue", timeout=5)
        except urllib.error.HTTPError as exc:
            check("serveur 404", exc.code == 404)
    finally:
        server.shutdown()
        server.server_close()

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — HTTP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
