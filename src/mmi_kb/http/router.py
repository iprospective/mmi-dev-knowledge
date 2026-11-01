"""Router minimal : methodes, chemins, parametres nommes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import unquote


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)

    def first(self, name: str, default: str = "") -> str:
        values = self.query.get(name) or []
        return values[0] if values else default


@dataclass
class Response:
    status: int = 200
    body: bytes = b""
    content_type: str = "application/json; charset=utf-8"
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def json(cls, data: Any, status: int = 200) -> "Response":
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        return cls(status=status, body=body)

    @classmethod
    def text(cls, text: str, status: int = 200) -> "Response":
        return cls(status=status, body=text.encode("utf-8"), content_type="text/plain; charset=utf-8")


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


Handler = Callable[[Request], Response]


class Router:
    def __init__(self):
        self.routes: list[tuple[str, re.Pattern[str], Handler]] = []

    def add(self, method: str, pattern: str, handler: Handler) -> None:
        regex = re.sub(
            r"<([A-Za-z_][A-Za-z0-9_]*)(?::([A-Za-z]+))?>",
            lambda m: f"(?P<{m.group(1)}>{'.+' if m.group(2) == 'path' else '[^/]+'})",
            pattern,
        )
        self.routes.append((method.upper(), re.compile(f"^{regex}$"), handler))

    def dispatch(
        self,
        method: str,
        path: str,
        query: dict[str, list[str]] | None = None,
    ) -> Response:
        method = method.upper()
        allowed = False
        for route_method, regex, handler in self.routes:
            match = regex.match(path)
            if not match:
                continue
            if route_method != method:
                allowed = True
                continue
            params = {key: unquote(value) for key, value in match.groupdict().items()}
            return handler(Request(method, path, query or {}, params))
        if allowed:
            raise HttpError(405, "methode non autorisee")
        raise HttpError(404, "route inconnue")
