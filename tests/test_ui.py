#!/usr/bin/env python3
"""Tests de l'UI read-only."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmi_kb.app import App  # noqa: E402
from mmi_kb.http.handlers import build_router  # noqa: E402

failures = 0


def check(label, cond):
    global failures
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond:
        failures += 1


def main():
    router = build_router(App(ROOT))
    root = router.dispatch("GET", "/", {})
    check("accueil HTML", root.status == 200 and b"<html" in root.body and b"mmi-kb" in root.body)
    check("API /api JSON", b'"name": "mmi-kb"' in router.dispatch("GET", "/api", {}).body)

    entities = router.dispatch("GET", "/ui/entities", {})
    check("liste fiches", entities.status == 200 and b"tool:dolibarr" in entities.body)

    detail = router.dispatch("GET", "/ui/entities/tool:dolibarr", {})
    check("détail fiche", detail.status == 200 and b"Dolibarr" in detail.body)

    quirk = router.dispatch("GET", "/ui/entities/quirk%3Adolibarr%2Fpdf-sponge-round-string", {})
    check("détail id avec slash", quirk.status == 200 and b"pdf_sponge" in quirk.body)

    search = router.dispatch("GET", "/ui/search", {"q": ["dolibarr"]})
    check("recherche", search.status == 200 and b"tool:dolibarr" in search.body)

    view = router.dispatch("GET", "/ui/views/docs", {})
    check("vue HTML", view.status == 200 and b"Vue" in view.body)

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — UI read-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
