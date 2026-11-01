#!/usr/bin/env python3
"""Tests de structure des contrats knowledge (sans dependance jsonschema)."""
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^(tool|component|version|compatibility|quirk|recipe|source|license|vendor):[a-z0-9][a-z0-9@/._-]*$")
VIEWS = {"docs", "tests", "agents", "compat", "catalog", "releases", "licenses", "sources"}


def check(label, cond):
    print(f"  {'✓' if cond else '✗'} {label}")
    return bool(cond)


def main():
    failures = 0
    task_schema = json.loads((ROOT / "schema/task-knowledge.schema.json").read_text())
    view_schema = json.loads((ROOT / "schema/view.schema.json").read_text())
    example = yaml.safe_load((ROOT / "examples/task-knowledge.yml").read_text())["knowledge"]
    view = json.loads((ROOT / "examples/view-compat.json").read_text())

    failures += not check("schema tache versionne", task_schema.get("$id", "").endswith("task-knowledge.schema.json"))
    failures += not check("action valide", example.get("action") in {"read", "update"})
    failures += not check("refs non vides", isinstance(example.get("refs"), list) and example["refs"])
    failures += not check("IDs valides", all(ID_RE.match(ref) for ref in example["refs"]))
    failures += not check("lock court", bool(re.fullmatch(r"[0-9a-f]{7,40}", example.get("lock", ""))))
    failures += not check("vue connue", view.get("view") in VIEWS)
    failures += not check("enveloppe v1", view.get("schema") == "mmi-kb.view/v1")
    failures += not check("commit present", bool(re.fullmatch(r"[0-9a-f]{7,40}", view.get("knowledge_commit", ""))))
    failures += not check("items liste", isinstance(view.get("items"), list))
    failures += not check("schema vue versionne", view_schema.get("$id", "").endswith("view.schema.json"))

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — contrats knowledge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
