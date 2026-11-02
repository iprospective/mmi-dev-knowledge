"""Routes HTML de consultation read-only."""

from __future__ import annotations

from ..app import App
from ..domain import KbError, public, tool_of
from ..views import VIEWS
from ..http.router import HttpError, Request, Response, Router
from . import render


def build_ui_routes(router: Router, app: App) -> None:
    def docs() -> list[dict]:
        rows, errors = app.repository.load_all()
        if errors:
            raise HttpError(500, "corpus invalide")
        return [public(doc, body=doc.get("kind") == "doc") for doc in rows]

    def index(_request: Request) -> Response:
        rows, errors = app.repository.load_all()
        if errors:
            raise HttpError(500, "corpus invalide")
        docs_public = [public(doc, body=doc.get("kind") == "doc") for doc in rows]
        from ..views import git_commit
        return Response.html(render.dashboard(docs_public, git_commit(app.root)))

    def entities(request: Request) -> Response:
        rows = docs()
        query = request.first("q").lower()
        tool = request.first("tool")
        kind = request.first("kind")
        status = request.first("status")
        if query:
            rows = [row for row in rows if query in (str(row.get("id", "")) + " " + str(row.get("title", "")) + " " + str(row.get("summary", ""))).lower()]
        if tool:
            rows = [row for row in rows if tool_of(row) == tool]
        if kind:
            rows = [row for row in rows if row.get("kind") == kind]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        return Response.html(render.entity_list(rows))

    def search(request: Request) -> Response:
        query = request.first("q")
        rows = docs()
        if query:
            needle = query.lower()
            rows = [row for row in rows if needle in (str(row.get("id", "")) + " " + str(row.get("title", "")) + " " + str(row.get("summary", ""))).lower()]
        return Response.html(render.entity_list(rows, f"Recherche : {query}" if query else "Recherche"))

    def entity(request: Request) -> Response:
        doc = app.repository.get(request.params["id"])
        if doc is None:
            raise HttpError(404, f"fiche introuvable : {request.params['id']}")
        data = public(doc, body=doc.get("kind") == "doc")
        return Response.html(render.entity_detail(data))

    def view(request: Request) -> Response:
        name = request.params["view"]
        if name not in VIEWS:
            raise HttpError(404, "vue inconnue")
        filters = {key: request.first(key) for key in ("tool", "version", "component", "php") if request.first(key)}
        try:
            data = app.views.build(name, filters)
        except KbError as exc:
            raise HttpError(500, str(exc)) from exc
        return Response.html(render.view_page(name, data))

    router.add("GET", "/", index)
    router.add("GET", "/ui", index)
    router.add("GET", "/ui/entities", entities)
    router.add("GET", "/ui/entities/<id:path>", entity)
    router.add("GET", "/ui/search", search)
    router.add("GET", "/ui/views/<view>", view)
