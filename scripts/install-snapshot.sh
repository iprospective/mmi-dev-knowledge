#!/bin/bash
# Installe un bundle KB dans le core PM (root).
#
# Usage :
#   sudo scripts/install-snapshot.sh
#   sudo scripts/install-snapshot.sh --source dist/kb-snapshot
#   sudo scripts/install-snapshot.sh --target /zfs/workspaces/.mmi-pm-core/knowledge/kb-snapshot
#   sudo scripts/install-snapshot.sh --dry-run
#
# Le bundle doit avoir ete genere avant :
#   bin/mmi-kb export --format bundle --out dist/kb-snapshot
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/dist/kb-snapshot"
TARGET="/zfs/workspaces/.mmi-pm-core/knowledge/kb-snapshot"
DRY_RUN=0
VERIFY=1
TS="$(date +%Y%m%d-%H%M%S)"

usage() {
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
    case "$1" in
        --source) SOURCE="${2:?source manquante}"; shift 2 ;;
        --target) TARGET="${2:?target manquant}"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --no-verify) VERIFY=0; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "option inconnue : $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "ERREUR : ce script doit tourner en root." >&2
    exit 1
fi

SOURCE="$(realpath -e "$SOURCE")"
TARGET="$(realpath -m "$TARGET")"
PARENT="$(dirname "$TARGET")"

if [ "$SOURCE" = "$TARGET" ]; then
    echo "ERREUR : source et cible identiques." >&2
    exit 1
fi
if [ -L "$TARGET" ]; then
    echo "ERREUR : la cible est un lien symbolique : $TARGET" >&2
    exit 1
fi
if [ ! -f "$SOURCE/manifest.json" ] || [ ! -f "$SOURCE/entities.jsonl" ] || [ ! -d "$SOURCE/views" ]; then
    echo "ERREUR : bundle incomplet : $SOURCE" >&2
    echo "  attendu : manifest.json, entities.jsonl, views/" >&2
    exit 1
fi
if find "$SOURCE" -type l -print -quit | grep -q .; then
    echo "ERREUR : le bundle contient un lien symbolique." >&2
    exit 1
fi

python3 - "$SOURCE" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
if manifest.get("schema") != "mmi-kb.bundle/v1":
    raise SystemExit("schema de bundle inattendu")
views = manifest.get("views") or []
if len(views) != 8 or not all((root / "views" / f"{view}.json").is_file() for view in views):
    raise SystemExit("les 8 vues sont absentes ou incompletes")
rows = [json.loads(line) for line in (root / "entities.jsonl").read_text().splitlines() if line.strip()]
if manifest.get("entities") != len(rows):
    raise SystemExit("compteur entities incoherent")
print(f"bundle valide : {len(rows)} entites, {len(views)} vues, commit {manifest.get('knowledge_commit', '?')}")
PY

echo "source : $SOURCE"
echo "cible  : $TARGET"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] aucune modification."
    exit 0
fi

install -d -o root -g root -m 755 "$PARENT"
TMP="$(mktemp -d "$PARENT/.kb-snapshot.tmp.XXXXXX")"
BACKUP=""
cleanup() {
    rm -rf "$TMP"
}
trap cleanup EXIT

cp -a "$SOURCE/." "$TMP/"
chown -R root:root "$TMP"
find "$TMP" -type d -exec chmod 755 {} +
find "$TMP" -type f -exec chmod 644 {} +

if [ -e "$TARGET" ]; then
    BACKUP="${TARGET}.bak-${TS}"
    mv "$TARGET" "$BACKUP"
    echo "ancien snapshot conserve : $BACKUP"
fi
mv "$TMP" "$TARGET"
trap - EXIT
chown -R root:root "$TARGET"
find "$TARGET" -type d -exec chmod 755 {} +
find "$TARGET" -type f -exec chmod 644 {} +
echo "snapshot installe : $TARGET"

if [ "$VERIFY" -eq 1 ]; then
    if command -v mmi-pm >/dev/null 2>&1; then
        mmi-pm knowledge --mode snapshot --snapshot "$TARGET" info
    else
        echo "mmi-pm introuvable : verification manuelle conseillee." >&2
    fi
fi
