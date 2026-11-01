#!/usr/bin/env python3
"""Tests du format documentaire Markdown + frontmatter."""
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmi_kb.app import App  # noqa: E402
from mmi_kb.domain import KbError  # noqa: E402

failures = 0


def check(label, cond):
    global failures
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond:
        failures += 1


FRONT = """---
id: doc:dolibarr/mep
kind: doc
doc_type: procedure
tool: dolibarr
title: Dolibarr — mise en production
summary: Procedure generique de MEP Dolibarr.
status: draft
provenance:
  source: https://github.com/Dolibarr/dolibarr
---

# Procedure

1. Verifier l'arbre git.
2. Deployer.
"""


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        path = root / "content/docs/dolibarr/mep.md"
        path.parent.mkdir(parents=True)
        path.write_text(FRONT, encoding="utf-8")
        app = App(root)
        docs, errors = app.repository.load_all()
        check("doc Markdown charge", not errors and len(docs) == 1)
        check("body conserve", "Verifier l'arbre git" in docs[0]["_body"])
        check("id doc", docs[0]["id"] == "doc/dolibarr/mep" or docs[0]["id"] == "doc:dolibarr/mep")
        view = app.views.build("docs", {"tool": "dolibarr"})
        check("doc dans la vue docs", len(view["items"]) == 1 and view["items"][0]["body"])
        entity = app.repository.get("doc:dolibarr/mep")
        check("get doc", entity is not None and entity.get("doc_type") == "procedure")

        path.write_text(FRONT.replace("title: Dolibarr — mise en production\n", "title: Dolibarr — mise en production\nticket: RM1234\n"), encoding="utf-8")
        _docs, errors = app.repository.load_all()
        check("reference ticket refusee", any("ticket" in error for error in errors))

        path.write_text("# sans frontmatter\n", encoding="utf-8")
        try:
            app.repository.load_all()
        except KbError:
            check("frontmatter manquant refuse", True)
        else:
            check("frontmatter manquant refuse", False)

    print()
    if failures:
        print(f"ECHEC : {failures} assertion(s)")
        return 1
    print("OK — documents Markdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
