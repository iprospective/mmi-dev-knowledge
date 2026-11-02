"""Petit rendu HTML server-side, sans framework front."""

from __future__ import annotations

import html
import json
from typing import Any
from urllib.parse import quote

from ..domain import public, summary_text, tool_of

try:
    from markdown_it import MarkdownIt
    _MD = MarkdownIt("commonmark", {"html": False})
except ImportError:  # pragma: no cover
    _MD = None

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;color:#17202a;background:#f6f7f9}
header{background:#1f2937;color:#fff;padding:1rem 1.5rem;display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap}
header a{color:#fff;text-decoration:none;font-weight:600}
header form{margin-left:auto;display:flex;gap:.4rem}
input,select,button{font:inherit;padding:.45rem .6rem;border:1px solid #cbd5e1;border-radius:6px}
button{cursor:pointer;background:#2563eb;color:#fff;border-color:#2563eb}
main{max-width:1100px;margin:1.5rem auto;padding:0 1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:1rem}
.card .num{font-size:1.8rem;font-weight:700}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}
th,td{padding:.6rem .75rem;border-bottom:1px solid #eef2f7;text-align:left;vertical-align:top}
th{background:#f1f5f9;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
.badge{display:inline-block;padding:.1rem .45rem;border-radius:999px;background:#e2e8f0;font-size:.8rem}
.muted{color:#64748b}
pre{background:#0f172a;color:#e2e8f0;padding:1rem;border-radius:10px;overflow:auto}
article{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:1.25rem 1.5rem}
article h1,article h2,article h3{line-height:1.2}
a{color:#1d4ed8}
"""


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def markdown(text: str) -> str:
    if _MD is not None:
        return _MD.render(text)
    return f"<pre>{_e(text)}</pre>"


def layout(title: str, body: str, query: str = "") -> str:
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)} · mmi-kb</title><style>{CSS}</style></head>
<body><header>
<a href="/">mmi-kb</a>
<a href="/ui/entities">Fiches</a>
<a href="/ui/views/docs">Docs</a>
<a href="/ui/views/tests">Tests</a>
<form action="/ui/search" method="get">
<input name="q" value="{_e(query)}" placeholder="Rechercher…" aria-label="Rechercher">
<button type="submit">Chercher</button>
</form>
</header><main>{body}</main></body></html>"""


def _label(doc: dict[str, Any]) -> str:
    return str(doc.get("title") or summary_text(doc.get("summary")) or doc.get("id", ""))


def entity_table(items: list[dict[str, Any]]) -> str:
    rows = []
    for doc in items:
        doc_id = str(doc.get("id", ""))
        href = "/ui/entities/" + quote(doc_id, safe="/:")
        rows.append(
            "<tr>"
            f"<td><a href=\"{href}\">{_e(doc_id)}</a></td>"
            f"<td>{_e(_label(doc))}</td>"
            f"<td>{_e(doc.get('kind', ''))}</td>"
            f"<td>{_e(tool_of(doc))}</td>"
            f"<td><span class=\"badge\">{_e(doc.get('status', ''))}</span></td>"
            "</tr>"
        )
    if not rows:
        return "<p class=\"muted\">Aucune fiche.</p>"
    return (
        "<table><thead><tr><th>ID</th><th>Titre</th><th>Kind</th><th>Outil</th>"
        "<th>Statut</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def dashboard(docs: list[dict[str, Any]], commit: str) -> str:
    tools: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for doc in docs:
        tools[tool_of(doc)] = tools.get(tool_of(doc), 0) + 1
        kinds[str(doc.get("kind", ""))] = kinds.get(str(doc.get("kind", "")), 0) + 1
    cards = "".join(
        f"<div class=\"card\"><div class=\"muted\">{_e(name)}</div><div class=\"num\">{count}</div></div>"
        for name, count in sorted(kinds.items())
    )
    tool_list = ", ".join(f"{_e(name)} ({count})" for name, count in sorted(tools.items()))
    return layout(
        "Accueil",
        f"<h1>Knowledge</h1><p class=\"muted\">commit <code>{_e(commit)}</code></p>"
        f"<div class=\"grid\">{cards}</div>"
        f"<h2>Outils</h2><p>{tool_list or '—'}</p>"
        "<h2>Dernières fiches</h2>" + entity_table(docs[:12]),
    )


def entity_list(docs: list[dict[str, Any]], title: str = "Fiches") -> str:
    return layout(title, f"<h1>{_e(title)}</h1>{entity_table(docs)}")


def entity_detail(doc: dict[str, Any]) -> str:
    meta = []
    for key in ("kind", "doc_type", "status", "confidence", "tool", "owner", "lifecycle"):
        if doc.get(key):
            meta.append(f"<tr><th>{_e(key)}</th><td>{_e(doc[key])}</td></tr>")
    if doc.get("applies_to"):
        meta.append(f"<tr><th>applies_to</th><td><pre>{_e(json.dumps(doc['applies_to'], ensure_ascii=False, indent=2))}</pre></td></tr>")
    body = doc.get("body") or doc.get("_body")
    if body:
        content = markdown(str(body))
    else:
        content = "<pre>" + _e(json.dumps(public(doc), ensure_ascii=False, indent=2, default=str)) + "</pre>"
    return layout(
        _label(doc),
        f"<h1>{_e(_label(doc))}</h1><p class=\"muted\">{_e(doc.get('id', ''))}</p>"
        f"<table>{''.join(meta)}</table><article>{content}</article>",
    )


def view_page(name: str, data: dict[str, Any]) -> str:
    return layout(
        f"Vue {name}",
        f"<h1>Vue <code>{_e(name)}</code></h1>"
        f"<p class=\"muted\">commit {_e(data.get('knowledge_commit', ''))}</p>"
        + entity_table(data.get("items", [])),
    )
