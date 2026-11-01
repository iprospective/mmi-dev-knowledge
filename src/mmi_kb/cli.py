"""CLI minimale de mmi-dev-knowledge."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - message utilisateur
    yaml = None

KINDS = {
    "tool",
    "component",
    "version",
    "compatibility",
    "quirk",
    "recipe",
    "source",
    "license",
    "vendor",
}

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_KEYS = {
    "client",
    "client_id",
    "customer",
    "customer_id",
    "project_id",
    "redmine",
    "task",
    "task_id",
    "ticket",
    "ticket_id",
    "secret",
    "password",
    "token",
    "credential",
    "credentials",
}


class KbError(Exception):
    pass


def root_from(value: str | None) -> Path:
    return Path(value or os.environ.get("MMI_KB_ROOT") or ROOT).resolve()


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise KbError("PyYAML requis : python3 -m pip install PyYAML")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise KbError(f"{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise KbError(f"{path}: la fiche doit etre un objet YAML")
    return data


def iter_docs(root: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    content = root / "content"
    if not content.is_dir():
        raise KbError(f"dossier content/ absent : {content}")
    for path in sorted(content.rglob("*.yml")) + sorted(content.rglob("*.yaml")):
        yield path, load_yaml(path)


def summary_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("fr") or value.get("en") or "")
    return ""


def walk_keys(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            yield str(key), here
            yield from walk_keys(child, here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{path}[{index}]")


def validate_doc(path: Path, doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(path.parents[1]) if len(path.parents) > 1 else path
    for field in ("id", "kind", "summary", "status", "provenance"):
        if not doc.get(field):
            errors.append(f"{rel}: champ requis manquant : {field}")

    doc_id = str(doc.get("id", ""))
    kind = str(doc.get("kind", ""))
    if kind and kind not in KINDS:
        errors.append(f"{rel}: kind inconnu : {kind}")
    if doc_id and kind and not doc_id.startswith(f"{kind}:"):
        errors.append(f"{rel}: id {doc_id!r} ne commence pas par {kind + ':'!r}")
    if doc.get("status") not in {"draft", "verified", "deprecated"}:
        errors.append(f"{rel}: status invalide : {doc.get('status')!r}")
    if doc.get("confidence") is not None and doc.get("confidence") not in {"low", "medium", "high"}:
        errors.append(f"{rel}: confidence invalide : {doc.get('confidence')!r}")

    provenance = doc.get("provenance")
    if provenance is not None and not isinstance(provenance, dict):
        errors.append(f"{rel}: provenance doit etre un objet")
    elif isinstance(provenance, dict) and not provenance.get("source"):
        errors.append(f"{rel}: provenance.source requis")

    for key, where in walk_keys(doc):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{rel}: cle interdite {where!r} (client/tache/secret)")
    return errors


def load_all(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    docs: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: dict[str, str] = {}
    for path, doc in iter_docs(root):
        rel = str(path.relative_to(root))
        doc["_path"] = rel
        doc["_file"] = str(path)
        errors.extend(validate_doc(path, doc))
        doc_id = str(doc.get("id", ""))
        if doc_id:
            if doc_id in seen:
                errors.append(f"{rel}: id duplique {doc_id!r} (deja dans {seen[doc_id]})")
            else:
                seen[doc_id] = rel
        docs.append(doc)
    return docs, errors


def tool_of(doc: dict[str, Any]) -> str:
    applies = doc.get("applies_to") or {}
    if isinstance(applies, dict) and applies.get("tool"):
        return str(applies["tool"])
    raw = str(doc.get("id", "")).split(":", 1)[-1]
    return raw.split("/", 1)[0]


def cmd_validate(root: Path, _args: argparse.Namespace) -> int:
    docs, errors = load_all(root)
    if errors:
        for error in errors:
            print(f"ERREUR {error}", file=sys.stderr)
        print(f"{len(errors)} erreur(s) sur {len(docs)} fiche(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(docs)} fiche(s)")
    return 0


def cmd_index(root: Path, _args: argparse.Namespace) -> int:
    docs, errors = load_all(root)
    if errors:
        for error in errors:
            print(f"ERREUR {error}", file=sys.stderr)
        return 1
    index_dir = root / "index"
    index_dir.mkdir(exist_ok=True)
    db_path = index_dir / "mmi-kb.sqlite"
    with sqlite3.connect(db_path) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS docs ("
            "id TEXT PRIMARY KEY, kind TEXT, path TEXT, summary TEXT, "
            "status TEXT, tool TEXT, version TEXT)"
        )
        db.execute("DELETE FROM docs")
        for doc in docs:
            db.execute(
                "INSERT INTO docs(id, kind, path, summary, status, tool, version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(doc["id"]),
                    str(doc.get("kind", "")),
                    str(doc["_path"]),
                    summary_text(doc.get("summary")),
                    str(doc.get("status", "")),
                    tool_of(doc),
                    str((doc.get("applies_to") or {}).get("versions", ""))
                    if isinstance(doc.get("applies_to"), dict)
                    else "",
                ),
            )
        db.commit()
    print(f"OK: {len(docs)} fiche(s) indexee(s) dans {db_path}")
    return 0


def cmd_search(root: Path, args: argparse.Namespace) -> int:
    query = f"%{args.query}%"
    db_path = root / "index" / "mmi-kb.sqlite"
    if db_path.is_file():
        with sqlite3.connect(db_path) as db:
            rows = db.execute(
                "SELECT id, summary FROM docs WHERE id LIKE ? OR summary LIKE ? "
                "ORDER BY id",
                (query, query),
            ).fetchall()
    else:
        docs, errors = load_all(root)
        if errors:
            raise KbError("corpus invalide, lancer validate")
        rows = [
            (str(d["id"]), summary_text(d.get("summary")))
            for d in docs
            if args.query.lower() in (str(d["id"]) + " " + summary_text(d.get("summary"))).lower()
        ]
    for doc_id, summary in rows:
        print(f"{doc_id}\t{summary}")
    return 0 if rows else 1


def cmd_show(root: Path, args: argparse.Namespace) -> int:
    docs, _errors = load_all(root)
    for doc in docs:
        if doc.get("id") == args.id:
            print(yaml.safe_dump({k: v for k, v in doc.items() if not k.startswith("_")}, sort_keys=False, allow_unicode=True))
            return 0
    print(f"introuvable : {args.id}", file=sys.stderr)
    return 1


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

    show = sub.add_parser("show", help="afficher une fiche par id")
    show.add_argument("id")
    show.set_defaults(func=cmd_show)

    get = sub.add_parser("get", help="alias de show")
    get.add_argument("id")
    get.set_defaults(func=cmd_show)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(root_from(args.root), args)
    except KbError as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
