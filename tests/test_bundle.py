#!/usr/bin/env python3
"""Tests du bundle KB destine au mode snapshot PM."""
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmi_kb.app import App  # noqa: E402
from mmi_kb.bundle import BundleExporter  # noqa: E402

VIEWS = {"docs", "tests", "agents", "compat", "catalog", "releases", "licenses", "sources"}
failures = 0


def check(label, cond):
    global failures
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond:
        failures += 1


def main():
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "bundle"
        BundleExporter(App(ROOT)).export(out)

        manifest = json.loads((out / "manifest.json").read_text())
        check("manifest schema", manifest.get("schema") == "mmi-kb.bundle/v1")
        check("manifest commit", bool(manifest.get("knowledge_commit")))
        check("manifest views", set(manifest.get("views", [])) == VIEWS)
        check("entities.jsonl", (out / "entities.jsonl").is_file())
        rows = [json.loads(line) for line in (out / "entities.jsonl").read_text().splitlines() if line]
        check("entites non vides", rows and all("_path" not in row for row in rows))
        for view in VIEWS:
            path = out / "views" / f"{view}.json"
            check(f"vue {view}", path.is_file() and json.loads(path.read_text())["view"] == view)

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — bundle KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
