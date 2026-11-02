# mmi-dev-knowledge

Knowledge transverse et **générique** des outils et plateformes utilisés par
iProspective : faits vérifiables, composants, versions, hooks/triggers, patterns,
quirks, recettes, sources et licences.

> Dépôt public : <https://github.com/iprospective/mmi-dev-knowledge>  
> Licence : GPL-3.0-or-later.

## Écosystème

`mmi-dev-knowledge` est utilisé **conjointement avec Karl/PM** — le même outil,
[`karl-ai-project-manager`](https://github.com/iprospective/karl-ai-project-manager)
— et avec TestKit. Karl/PM est le **gestionnaire de projet assisté par IA, modulaire** :
il porte le projet, les tâches, les décisions, les environnements et les workflows.
TestKit lit les recettes et quirks, BK fournit les faits produits. BK ne remplace
pas Karl/PM.

## Règles

- Aucun client, projet, tâche, ticket, secret ou credential.
- Un cas client est abstrait avant d'entrer ici ; le cas concret reste dans PM.
- Chaque fiche a un `id` stable, un `kind`, un `summary`, un `status` et une
  `provenance`.
- Les docs de projet/évolution restent dans PM + wiki Redmine.

## Structure

```text
schema/                  JSON Schema des kinds + contrats
examples/                exemples de bloc tâche et de vue
content/docs/            documents Markdown + frontmatter (kind doc)
content/tools/           fiches outil
content/quirks/          comportements inattendus et remédiations
content/recipes/         recettes de test génériques
content/vendors/         éditeurs/communautés
content/licenses/        licences et obligations
collectors/              collecte optionnelle par plateforme
src/mmi_kb/              CLI, API et UI
src/mmi_kb/ui/           pages HTML read-only
tests/                   tests de structure des contrats
index/                    index SQLite généré, non versionné
```

## Contrats

- `schema/task-knowledge.schema.json` : bloc `knowledge` d'une tâche PM.
- `schema/view.schema.json` : enveloppe `mmi-kb.view/v1`.
- Le contrat fonctionnel est dans PM et dans le wiki `knowledge-base`
  (`Contrat-knowledge`).

## CLI

```bash
bin/mmi-kb validate
bin/mmi-kb index
bin/mmi-kb search dolibarr
bin/mmi-kb show quirk:dolibarr/pdf-sponge-round-string
bin/mmi-kb view tests --tool dolibarr --format json
bin/mmi-kb export --format bundle --out dist/kb-snapshot
bin/mmi-kb serve --host 127.0.0.1 --port 8091
```

UI : `http://127.0.0.1:8091/` (accueil, fiches, recherche, vues).
API : `/api`, `/health`, `/views/<view>`, `/entities/<id>`.

Prérequis : Python 3.10+, PyYAML, markdown-it-py.

## Licence

Code et contenu : GPL-3.0-or-later (décision du 2026-11-01).
