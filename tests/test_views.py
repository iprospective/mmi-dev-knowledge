#!/usr/bin/env python3
"""Tests des vues generiques."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmi_kb.app import App  # noqa: E402
from mmi_kb.domain import KbError, tool_of  # noqa: E402

VIEWS = ["docs", "tests", "agents", "compat", "catalog", "releases", "licenses", "sources"]
failures = 0


def check(label, cond):
    global failures
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond:
        failures += 1


def main():
    app = App(ROOT)
    for view in VIEWS:
        data = app.views.build(view)
        check(f"{view} : enveloppe", data["schema"] == "mmi-kb.view/v1" and data["view"] == view)
        check(f"{view} : commit", bool(re.fullmatch(r"[0-9a-f]{7,40}", data["knowledge_commit"])))
        check(f"{view} : items", isinstance(data["items"], list))
        check(f"{view} : pas de chemin interne", all("_path" not in item for item in data["items"]))

    docs = app.views.build("docs", {"tool": "dolibarr"})
    check("filtre tool", docs["items"] and all(tool_of(item) == "dolibarr" for item in docs["items"]))

    try:
        app.views.build("inconnue")
    except KbError:
        check("vue inconnue refusee", True)
    else:
        check("vue inconnue refusee", False)

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — vues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
