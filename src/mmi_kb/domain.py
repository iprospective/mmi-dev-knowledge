"""Regles metier communes au CLI et a l'API."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
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
    "doc",
}
VIEWS = {"docs", "tests", "agents", "compat", "catalog", "releases", "licenses", "sources"}
DOC_TYPES = {
    "overview",
    "api",
    "procedure",
    "runbook",
    "reference",
    "tutorial",
    "explanation",
    "howto",
    "test_protocol",
    "test_surface",
    "guide",
}
ID_RE = re.compile(
    r"^(tool|component|version|compatibility|quirk|recipe|source|license|vendor|doc):"
    r"[a-z0-9][a-z0-9@/._-]*$"
)
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
    """Erreur utilisateur, sans trace technique."""


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


def summary_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("fr") or value.get("en") or "")
    return ""


def tool_of(doc: dict[str, Any]) -> str:
    applies = doc.get("applies_to") or {}
    if isinstance(applies, dict) and applies.get("tool"):
        return str(applies["tool"])
    raw = str(doc.get("id", "")).split(":", 1)[-1]
    return raw.split("/", 1)[0]


def walk_keys(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            yield str(key), here
            yield from walk_keys(child, here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{path}[{index}]")


def validate_doc(doc: dict[str, Any], rel: str) -> list[str]:
    errors: list[str] = []
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
    if kind == "doc":
        if not doc.get("title"):
            errors.append(f"{rel}: champ requis pour un doc : title")
        if doc.get("doc_type") not in DOC_TYPES:
            errors.append(f"{rel}: doc_type invalide : {doc.get('doc_type')!r}")
        if not str(doc.get("_body", "")).strip():
            errors.append(f"{rel}: corps Markdown vide")

    provenance = doc.get("provenance")
    if provenance is not None and not isinstance(provenance, dict):
        errors.append(f"{rel}: provenance doit etre un objet")
    elif isinstance(provenance, dict) and not provenance.get("source"):
        errors.append(f"{rel}: provenance.source requis")

    for key, where in walk_keys(doc):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{rel}: cle interdite {where!r} (client/tache/secret)")
    return errors


def public(doc: dict[str, Any], body: bool = False) -> dict[str, Any]:
    out = {key: value for key, value in doc.items() if not key.startswith("_")}
    if body and "_body" in doc:
        out["body"] = doc["_body"]
    return out
