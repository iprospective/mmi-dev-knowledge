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
        return (
            sorted(self.content.rglob("*.yml"))
            + sorted(self.content.rglob("*.yaml"))
            + sorted(self.content.rglob("*.md"))
        )

    def load_doc(self, path: Path) -> dict[str, Any]:
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                raise KbError(f"{path}: frontmatter YAML absent")
            end = text.find("\n---", 4)
            if end == -1:
                raise KbError(f"{path}: frontmatter non ferme")
            front = text[4:end]
            body = text[end + 4:].lstrip("\n")
            try:
                import yaml
                doc = yaml.safe_load(front) or {}
            except Exception as exc:
                raise KbError(f"{path}: frontmatter invalide : {exc}") from exc
            if not isinstance(doc, dict):
                raise KbError(f"{path}: frontmatter non objet")
            doc["_body"] = body
        else:
            doc = load_yaml(path)
        doc["_path"] = str(path.relative_to(self.root))
        doc["_file"] = str(path)
        return doc

    def docs(self) -> list[tuple[Path, dict[str, Any]]]:
        return [(path, self.load_doc(path)) for path in self.paths()]

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
