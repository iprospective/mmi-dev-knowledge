#!/usr/bin/env python3
"""Migre la knowledge PM generique vers le corpus BK (RM3600).

Les documents sont importes en `draft`, sanitisés (client/instance/ticket) et
doivent etre revus avant `verified`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

SOURCE = Path("/zfs/workspaces/.mmi-pm-core/knowledge")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content"

DOCS = {
    "dolibarr/mep.md": ("doc:dolibarr/mep", "procedure", "dolibarr", "Dolibarr — mise en production", "Procédure générique de MEP Dolibarr."),
    "dolibarr/env-dev.md": ("doc:dolibarr/env-dev-recettable", "howto", "dolibarr", "Dolibarr — rendre un env de dev recettable", "Rendre un environnement de dev testable par un agent."),
    "gitlab/api.md": ("doc:gitlab/api-pitfalls", "reference", "gitlab", "GitLab — API, pièges de résolution", "Pièges de résolution de projet et d'appels API GitLab."),
    "gitlab/depots-et-groupes.md": ("doc:gitlab/repo-layout", "reference", "gitlab", "GitLab — dépôts, groupes et anciens chemins", "Où chercher un dépôt et pourquoi un ancien chemin trompe."),
    "redmine/overview.md": ("doc:redmine/overview", "overview", "redmine", "Redmine — vue technique", "Modèle de données, terminologie et installation Redmine."),
    "redmine/api.md": ("doc:redmine/api", "reference", "redmine", "Redmine — API REST", "Authentification, endpoints et payloads Redmine."),
    "redmine/gotchas.md": ("doc:redmine/gotchas", "reference", "redmine", "Redmine — pièges connus", "Comportements inattendus de Redmine et remédiations."),
    "redmine/etiquettes.md": ("doc:redmine/tags", "reference", "redmine", "Redmine — étiquettes", "Conventions génériques d'étiquetage Redmine."),
    "redmine/textile-to-markdown-migration.md": ("doc:redmine/textile-markdown", "procedure", "redmine", "Redmine — migration Textile vers Markdown", "Procédure de migration des contenus Redmine."),
    "zabbix/api.md": ("doc:zabbix/api", "reference", "zabbix", "Zabbix — API JSON-RPC", "Accès API, recherche peu fiable et pièges de triggers."),
    "karl-agent/sessions.md": ("doc:karl-agent/sessions", "procedure", "karl-agent", "Karl — sessions et stockage", "Où vivent les sessions, ce qui est partagé et comment les déplacer."),
    "prestashop/mep.md": ("doc:prestashop/mep", "procedure", "prestashop", "PrestaShop — mise en production", "Procédure générique de MEP PrestaShop."),
    "prestashop/test-protocol.md": ("doc:prestashop/test-protocol", "test_protocol", "prestashop", "PrestaShop — protocole de test", "Surface de test et non-régression PrestaShop."),
    "mail/migration-imap.md": ("doc:mail/imap-migration", "procedure", "mail", "Mail — migration IMAP", "Migration additive de boîtes IMAP et pièges associés."),
    "migration/configurations-locales.md": ("doc:ops/local-config-migration", "procedure", "ops", "Migration — configurations locales", "Migrer les configurations locales sans perdre les secrets."),
    "dovecot/sieve-karl.md": ("doc:dovecot/sieve", "reference", "dovecot", "Dovecot / Sieve — boîte et filtres", "Fonctionnement générique d'une boîte Sieve."),
    "zfs/sauvegarde.md": ("doc:zfs/backup", "procedure", "zfs", "ZFS — sauvegarde et snapshots", "Snapshots, rétention et restauration ZFS."),
    "opensvc/bascule-conteneur.md": ("doc:opensvc/container-switch", "procedure", "opensvc", "OpenSVC — bascule de conteneur", "Basculer un conteneur d'un nœud à l'autre."),
    "gnupg/gpg-agent-ssh.md": ("doc:gnupg/agent-ssh", "reference", "gnupg", "GnuPG — gpg-agent en ssh-agent", "Pièges headless de gpg-agent en émulation ssh-agent."),
}

REPLACEMENTS = [
    ("gitlab.iprospective.fr", "<gitlab-instance>"),
    ("tasks.iprospective.fr", "<redmine-instance>"),
    ("zabbix.iprospective.fr", "<zabbix-instance>"),
    ("erp.calicote.com", "<client-instance>"),
    ("erp.dercya.com", "<client-instance>"),
    ("erp.villa-cactus.com", "<client-instance>"),
    ("mmi.iprospective.net", "<host>"),
    ("dev.lxc", "<dev-host>"),
    ("10.0.3.11", "<ip>"),
    ("srv5", "<host>"),
    ("srv4", "<host>"),
    ("srv3", "<host>"),
    ("Calicote", "<client>"),
    ("calicote", "<client>"),
    ("Dercya", "<client>"),
    ("dercya", "<client>"),
    ("Villa Cactus", "<client>"),
    ("villa-cactus", "<client>"),
    ("Pisceen", "<client>"),
    ("pisceen", "<client>"),
    ("Calyclay", "<client>"),
    ("calyclay", "<client>"),
    ("CalyClay", "<client>"),
    ("@iprospective.fr", "@<domain>"),
    ("-rm3039", "-rm<ticket>"),
]


def sanitize(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    text = re.sub(r"\bRM\d+\b", "un ticket", text)
    text = re.sub(r"^refs:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^ticket:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^tracks:.*$", "", text, flags=re.MULTILINE)
    return text


def body_without_frontmatter(text: str) -> str:
    match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[match.end():] if match else text


def title_of(body: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def write_doc(rel: str, meta: tuple[str, str, str, str, str]) -> Path:
    doc_id, doc_type, tool, title, summary = meta
    src = SOURCE / rel
    body = sanitize(body_without_frontmatter(src.read_text(encoding="utf-8")))
    title = sanitize(title_of(body, title))
    front = {
        "id": doc_id,
        "kind": "doc",
        "doc_type": doc_type,
        "title": title,
        "summary": summary,
        "tool": tool,
        "status": "draft",
        "owner": "iprospective",
        "audience": ["dev", "ops"],
        "provenance": {"source": "internal", "fetched_at": "2026-11-02"},
    }
    out = OUT / "docs" / f"{doc_id.split(':', 1)[1]}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) + "---\n\n" + body.strip() + "\n", encoding="utf-8")
    return out


def write_recipe() -> Path:
    source = yaml.safe_load((SOURCE / "prestashop/test-surface.yml").read_text(encoding="utf-8"))
    out = OUT / "recipes/prestashop/test-surface.yml"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": "recipe:prestashop/test-surface",
        "kind": "recipe",
        "recipe_type": "test_surface",
        "summary": "Surface de test générique PrestaShop.",
        "tool": "prestashop",
        "status": "draft",
        "owner": "iprospective",
        "provenance": {"source": "internal", "fetched_at": "2026-11-02"},
        "surface": source,
    }
    out.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def main() -> int:
    written = []
    for rel, meta in DOCS.items():
        written.append(write_doc(rel, meta))
    written.append(write_recipe())
    print(f"{len(written)} fichiers migres en draft :")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
