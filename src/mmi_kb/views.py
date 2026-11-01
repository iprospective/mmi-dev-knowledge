"""Construction des vues generiques consommees par PM et TestKit."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain import VIEWS, KbError, public, tool_of
from .repository import YamlRepository

VIEW_KINDS = {
    "docs": {"tool", "component", "version", "quirk", "recipe", "source", "license", "vendor"},
    "tests": {"recipe", "quirk"},
    "agents": {"tool", "component", "version", "quirk", "recipe"},
    "compat": {"compatibility"},
    "catalog": {"component"},
    "releases": {"version"},
    "licenses": {"license"},
    "sources": {"source"},
}


def git_commit(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short=12", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0000000"


def _matches(doc: dict[str, Any], filters: dict[str, str]) -> bool:
    applies = doc.get("applies_to") if isinstance(doc.get("applies_to"), dict) else {}
    if filters.get("tool") and tool_of(doc) != filters["tool"]:
        return False
    if filters.get("component"):
        component = str(applies.get("component", ""))
        if filters["component"] not in (component, str(doc.get("id", ""))):
            return False
    if filters.get("version"):
        versions = str(applies.get("versions", ""))
        if filters["version"] not in versions and filters["version"] != str(doc.get("id", "")).split("/")[-1]:
            return False
    if filters.get("php"):
        php = str(applies.get("php", ""))
        if filters["php"] not in php:
            return False
    return True


class ViewService:
    def __init__(self, repository: YamlRepository):
        self.repository = repository

    def build(self, view: str, filters: dict[str, str] | None = None) -> dict[str, Any]:
        if view not in VIEWS:
            raise KbError(f"vue inconnue : {view}")
        filters = {key: value for key, value in (filters or {}).items() if value}
        docs, errors = self.repository.load_all()
        if errors:
            raise KbError("corpus invalide : " + "; ".join(errors[:3]))
        items = [
            public(doc)
            for doc in docs
            if doc.get("kind") in VIEW_KINDS[view] and _matches(doc, filters)
        ]
        return {
            "schema": "mmi-kb.view/v1",
            "view": view,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "knowledge_commit": git_commit(self.repository.root),
            "filters": filters,
            "items": items,
        }
