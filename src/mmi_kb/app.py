"""Conteneur applicatif partage par le CLI et l'API."""

from __future__ import annotations

from pathlib import Path

from .index import SqliteIndex
from .repository import YamlRepository
from .views import ViewService


class App:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.repository = YamlRepository(self.root)
        self.index = SqliteIndex(self.root)
        self.views = ViewService(self.repository)
