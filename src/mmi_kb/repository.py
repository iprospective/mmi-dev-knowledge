"""Chargement du corpus YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .domain import KbError, load_yaml, validate_doc


class YamlRepository:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.content = self.root / "content"

    def paths(self) -> list[Path]:
        if not self.content.is_dir():
            raise KbError(f"dossier content/ absent : {self.content}")
        return sorted(self.content.rglob("*.yml")) + sorted(self.content.rglob("*.yaml"))

    def docs(self) -> list[tuple[Path, dict[str, Any]]]:
        rows = []
        for path in self.paths():
            doc = load_yaml(path)
            doc["_path"] = str(path.relative_to(self.root))
            doc["_file"] = str(path)
            rows.append((path, doc))
        return rows

    def load_all(self) -> tuple[list[dict[str, Any]], list[str]]:
        docs: list[dict[str, Any]] = []
        errors: list[str] = []
        seen: dict[str, str] = {}
        for path, doc in self.docs():
            rel = str(path.relative_to(self.root))
            errors.extend(validate_doc(doc, rel))
            doc_id = str(doc.get("id", ""))
            if doc_id:
                if doc_id in seen:
                    errors.append(f"{rel}: id duplique {doc_id!r} (deja dans {seen[doc_id]})")
                else:
                    seen[doc_id] = rel
            docs.append(doc)
        return docs, errors

    def get(self, doc_id: str) -> dict[str, Any] | None:
        docs, _errors = self.load_all()
        for doc in docs:
            if doc.get("id") == doc_id:
                return doc
        return None
