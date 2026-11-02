"""Export d'un bundle KB lisible par PM sans mmi-kb."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .app import App
from .domain import KbError, public
from .views import VIEWS, git_commit


class BundleExporter:
    def __init__(self, app: App):
        self.app = app

    def export(self, out: Path) -> Path:
        docs, errors = self.app.repository.load_all()
        if errors:
            raise KbError("corpus invalide : " + "; ".join(errors[:3]))
        out = Path(out).resolve()
        views_dir = out / "views"
        views_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema": "mmi-kb.bundle/v1",
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "knowledge_commit": git_commit(self.app.root),
            "entities": len(docs),
            "views": sorted(VIEWS),
        }
        (out / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with (out / "entities.jsonl").open("w", encoding="utf-8") as handle:
            for doc in docs:
                entity = public(doc, body=doc.get("kind") == "doc")
                handle.write(json.dumps(entity, ensure_ascii=False, default=str) + "\n")

        for view in sorted(VIEWS):
            data = self.app.views.build(view)
            (views_dir / f"{view}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
        return out
