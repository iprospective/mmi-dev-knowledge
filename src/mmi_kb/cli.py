"""CLI minimale de mmi-dev-knowledge."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .app import App
from .domain import KbError, public, summary_text
from .views import VIEWS

ROOT = Path(__file__).resolve().parents[2]


def root_from(value: str | None) -> Path:
    return Path(value or os.environ.get("MMI_KB_ROOT") or ROOT).resolve()


def cmd_validate(app: App, _args: argparse.Namespace) -> int:
    docs, errors = app.repository.load_all()
    if errors:
        for error in errors:
            print(f"ERREUR {error}", file=sys.stderr)
        print(f"{len(errors)} erreur(s) sur {len(docs)} fiche(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(docs)} fiche(s)")
    return 0


def cmd_index(app: App, _args: argparse.Namespace) -> int:
    docs, errors = app.repository.load_all()
    if errors:
        for error in errors:
            print(f"ERREUR {error}", file=sys.stderr)
        return 1
    path = app.index.build(docs)
    print(f"OK: {len(docs)} fiche(s) indexee(s) dans {path}")
    return 0


def cmd_search(app: App, args: argparse.Namespace) -> int:
    rows = app.index.search(args.query)
    if not rows:
        docs, errors = app.repository.load_all()
        if errors:
            raise KbError("corpus invalide, lancer validate")
        needle = args.query.lower()
        rows = [
            (str(doc["id"]), summary_text(doc.get("summary")))
            for doc in docs
            if needle in (str(doc["id"]) + " " + summary_text(doc.get("summary"))).lower()
        ]
    for doc_id, summary in rows:
        print(f"{doc_id}\t{summary}")
    return 0 if rows else 1


def cmd_show(app: App, args: argparse.Namespace) -> int:
    doc = app.repository.get(args.id)
    if doc is None:
        print(f"introuvable : {args.id}", file=sys.stderr)
        return 1
    import yaml
    print(yaml.safe_dump(public(doc), sort_keys=False, allow_unicode=True))
    return 0


def cmd_view(app: App, args: argparse.Namespace) -> int:
    filters = {
        key: getattr(args, key)
        for key in ("tool", "version", "component", "php")
        if getattr(args, key)
    }
    data = app.views.build(args.view, filters)
    if args.format == "markdown":
        print(f"# Vue `{data['view']}`")
        print(f"\ncommit : `{data['knowledge_commit']}`  ")
        print(f"filtres : `{json.dumps(data['filters'], ensure_ascii=False)}`\n")
        for item in data["items"]:
            print(f"- `{item['id']}` — {summary_text(item.get('summary'))}")
        return 0
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_serve(app: App, args: argparse.Namespace) -> int:
    from .http.server import serve
    serve(app, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mmi-kb", description=__doc__)
    parser.add_argument("--root", help="racine du depot (defaut : MMI_KB_ROOT ou racine du script)")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="valider le corpus")
    validate.set_defaults(func=cmd_validate)

    index = sub.add_parser("index", help="construire l'index SQLite")
    index.set_defaults(func=cmd_index)

    search = sub.add_parser("search", help="rechercher dans l'index ou le corpus")
    search.add_argument("query")
    search.set_defaults(func=cmd_search)

    for name, help_text in (("show", "afficher une fiche par id"), ("get", "alias de show")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("id")
        cmd.set_defaults(func=cmd_show)

    view = sub.add_parser("view", help="construire une vue generique")
    view.add_argument("view", choices=sorted(VIEWS))
    view.add_argument("--tool")
    view.add_argument("--version")
    view.add_argument("--component")
    view.add_argument("--php")
    view.add_argument("--format", choices=("json", "markdown"), default="json")
    view.set_defaults(func=cmd_view)

    serve = sub.add_parser("serve", help="servir l'API read-only")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8091)
    serve.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = App(root_from(args.root))
    try:
        return args.func(app, args)
    except KbError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
