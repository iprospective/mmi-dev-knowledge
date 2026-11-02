"""Handlers HTTP : aucune logique metier, uniquement l'adaptation des services."""

from __future__ import annotations

from ..app import App
from ..domain import KbError, public
from ..views import git_commit
from .router import HttpError, Request, Response, Router
from ..ui.handlers import build_ui_routes


def build_router(app: App) -> Router:
    router = Router()

    def root(_request: Request) -> Response:
        return Response.json({
            "name": "mmi-kb",
            "status": "ok",
            "endpoints": ["/ui", "/health", "/commit", "/views/<view>", "/entities/<id>"],
        })

    def health(_request: Request) -> Response:
        return Response.json({
            "status": "ok",
            "knowledge_commit": git_commit(app.root),
            "indexed": app.index.count(),
        })

    def commit(_request: Request) -> Response:
        return Response.json({"knowledge_commit": git_commit(app.root)})

    def view(request: Request) -> Response:
        filters = {
            key: request.first(key)
            for key in ("tool", "version", "component", "php")
            if request.first(key)
        }
        try:
            return Response.json(app.views.build(request.params["view"], filters))
        except KbError as exc:
            raise HttpError(404 if "inconnue" in str(exc) else 400, str(exc)) from exc

    def entity(request: Request) -> Response:
        doc = app.repository.get(request.params["id"])
        if doc is None:
            raise HttpError(404, f"fiche introuvable : {request.params['id']}")
        return Response.json(public(doc, body=doc.get("kind") == "doc"))

    router.add("GET", "/api", root)
    router.add("GET", "/health", health)
    router.add("GET", "/commit", commit)
    router.add("GET", "/views/<view>", view)
    router.add("GET", "/entities/<id:path>", entity)
    build_ui_routes(router, app)
    return router
