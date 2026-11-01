# mmi-dev-knowledge

Knowledge transverse et **générique** des outils et plateformes utilisés par
iProspective : faits vérifiables, composants, versions, hooks/triggers, patterns,
quirks, recettes, sources et licences.

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
src/mmi_kb/              CLI
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
bin/mmi-kb serve --host 127.0.0.1 --port 8091
```

Prérequis : Python 3.9+, PyYAML.

## Licence

Code et contenu : GPL-3.0-or-later (décision du 2026-11-01).
