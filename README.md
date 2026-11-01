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
schema/                  JSON Schema des kinds
content/tools/           fiches outil
content/quirks/          comportements inattendus et remédiations
content/recipes/         recettes de test génériques
content/vendors/         éditeurs/communautés
content/licenses/        licences et obligations
collectors/              collecte optionnelle par plateforme
src/mmi_kb/              CLI
index/                    index SQLite généré, non versionné
```

## CLI

```bash
bin/mmi-kb validate
bin/mmi-kb index
bin/mmi-kb search dolibarr
bin/mmi-kb show quirk:dolibarr/pdf-sponge-round-string
```

Prérequis : Python 3.9+, PyYAML.

## Licence

Code et contenu : GPL-3.0-or-later (décision du 2026-11-01).
