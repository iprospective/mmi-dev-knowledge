"""Index SQLite reconstructible depuis le corpus Git."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .domain import summary_text, tool_of


class SqliteIndex:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.path = self.root / "index" / "mmi-kb.sqlite"

    def build(self, docs: list[dict[str, Any]]) -> Path:
        self.path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS docs ("
                "id TEXT PRIMARY KEY, kind TEXT, path TEXT, summary TEXT, "
                "status TEXT, tool TEXT, version TEXT)"
            )
            db.execute("DELETE FROM docs")
            for doc in docs:
                applies = doc.get("applies_to") if isinstance(doc.get("applies_to"), dict) else {}
                db.execute(
                    "INSERT INTO docs(id, kind, path, summary, status, tool, version) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(doc["id"]),
                        str(doc.get("kind", "")),
                        str(doc.get("_path", "")),
                        summary_text(doc.get("summary")),
                        str(doc.get("status", "")),
                        tool_of(doc),
                        str(applies.get("versions", "")),
                    ),
                )
            db.commit()
        return self.path

    def search(self, query: str) -> list[tuple[str, str]]:
        if not self.path.is_file():
            return []
        pattern = f"%{query}%"
        with sqlite3.connect(self.path) as db:
            return db.execute(
                "SELECT id, summary FROM docs WHERE id LIKE ? OR summary LIKE ? ORDER BY id",
                (pattern, pattern),
            ).fetchall()

    def count(self) -> int:
        if not self.path.is_file():
            return 0
        with sqlite3.connect(self.path) as db:
            return int(db.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
