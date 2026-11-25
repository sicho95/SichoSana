#!/bin/sh
# SichoSana v2.3.1 — livraison intégrale depuis un commit GitHub, sans Git ni ZIP local.
# --check : vérifie uniquement les fichiers et les tests. --apply : vérifie puis déploie.
set -eu
umask 077
MODE=${1:---check}
case "$MODE" in --check|--apply) ;; *) echo 'Usage: sh installer.sh --check|--apply' >&2; exit 2;; esac
REF=${SICHOSANA_REF:-}
APP=${SICHOSANA_APP_DIR:-/share/CE_CACHEDEV1_DATA/SichoSana/app}
BASE=$(dirname "$APP")
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')-$$
ARCHIVE="https://codeload.github.com/sicho95/SichoSana/tar.gz/$REF"
LOCK="$BASE/.sichosana-v231-install.lock"
STAGE="$BASE/.sichosana-v231-stage-$STAMP"
BACKUP="$BASE/backups/app-before-v231-$STAMP"
CANDIDATE="sichosana:v231-candidate-$STAMP"
OLDTAG="sichosana:backup-$STAMP"
SMOKE="sichosana-v231-smoke-$$"
ITEMS='static server scripts docs tests Dockerfile .dockerignore README.md'
LOCKED=0; STARTED=0; SUCCESS=0; SMOKE_STARTED=0; BUILT=0; TAGGED=0
log(){ printf '[SichoSana v2.3.1] %s\n' "$*"; }
error(){ printf '[ERREUR] %s\n' "$*" >&2; exit 1; }
compose(){ docker compose --project-directory "$APP" -f "$APP/compose.yaml" -p sichosana "$@"; }
rollback(){
    log "Retour arrière des fichiers et de l’image Docker. SQLite n’est pas écrasée."
    ok=1
    mkdir -p "$BACKUP/failed-new" || ok=0
    for item in $ITEMS; do
        if [ -e "$BACKUP/$item" ] || [ -e "$BACKUP/absent/$item" ]; then
            if [ -e "$APP/$item" ]; then mv "$APP/$item" "$BACKUP/failed-new/$item" || { ok=0; continue; }; fi
            if [ -e "$BACKUP/$item" ]; then mv "$BACKUP/$item" "$APP/$item" || ok=0; fi
        fi
    done
    if [ "$TAGGED" = 1 ]; then
        docker tag "$OLDTAG" "$IMAGE" && compose up -d --no-deps --no-build --pull never --force-recreate sichosana || ok=0
    fi
    if [ "$ok" = 1 ]; then log "Retour arrière des sources effectué : $BACKUP"; else log "Retour arrière incomplet : sauvegarde à $BACKUP ; consulter docker logs sichosana-app"; fi
}
cleanup(){
    rc=$?; trap - EXIT HUP INT TERM; set +e
    if [ "$STARTED" = 1 ] && [ "$SUCCESS" != 1 ]; then rollback; fi
    if [ "$SMOKE_STARTED" = 1 ]; then docker rm -f "$SMOKE" >/dev/null 2>&1; fi
    if [ "$BUILT" = 1 ]; then docker image rm "$CANDIDATE" >/dev/null 2>&1; fi
    if [ "$LOCKED" = 1 ]; then rm -rf "$STAGE"; rmdir "$LOCK"; fi
    exit "$rc"
}
printf '%s\n' "$REF" | grep -Eq '^[0-9a-f]{40}$' || error 'SICHOSANA_REF doit être un SHA GitHub complet (40 caractères).'
[ -d "$APP" ] && [ -f "$APP/.env" ] && [ -f "$APP/compose.yaml" ] || error "Installation ou configuration absente : $APP"
command -v docker >/dev/null 2>&1 || error 'Docker indisponible'
docker compose version >/dev/null 2>&1 || error 'Docker Compose indisponible'
docker inspect sichosana-app >/dev/null 2>&1 || error 'Conteneur sichosana-app absent'
mkdir "$LOCK" || error 'Une autre mise à jour est en cours (ou verrou résiduel).'
LOCKED=1
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
[ ! -e "$STAGE" ] || error 'Dossier de préparation déjà existant'
mkdir -p "$STAGE/src"
log "1/7 — Téléchargement unique depuis GitHub : $REF"
docker run --rm -i --network bridge -e ARCHIVE="$ARCHIVE" -v "$STAGE:/stage" python:3.12-slim python - <<'PY'
import os,pathlib,tarfile,urllib.request,shutil
root=pathlib.Path('/stage'); target=root/'src'; archive=root/'source.tar.gz'
req=urllib.request.Request(os.environ['ARCHIVE'],headers={'User-Agent':'SichoSana-QNAP-v231'})
with urllib.request.urlopen(req,timeout=90) as response, archive.open('wb') as f:
    total=0
    while True:
        b=response.read(1024*1024)
        if not b: break
        total+=len(b)
        if total>150_000_000: raise SystemExit('Archive trop volumineuse')
        f.write(b)
if total<10000:raise SystemExit('Archive GitHub trop petite')
with tarfile.open(archive,'r:gz') as t:
    seen=set(); expanded=0
    for member in t:
        if member.isdir():continue
        if not member.isfile():raise SystemExit('Type de membre interdit: '+member.name)
        parts=pathlib.PurePosixPath(member.name).parts
        if len(parts)<2 or member.name.startswith('/') or '..' in parts:raise SystemExit('Chemin archive invalide')
        rel=pathlib.PurePosixPath(*parts[1:]); dest=target.joinpath(*rel.parts)
        if str(rel) in seen or member.size>30_000_000:raise SystemExit('Membre dupliqué ou trop volumineux')
        seen.add(str(rel)); expanded+=member.size
        if expanded>300_000_000:raise SystemExit('Archive décompressée trop volumineuse')
        if rel.parts[0] in ('.env','runtime','.data','.git'):raise SystemExit('Donnée privée interdite dans la livraison')
        if not dest.resolve().is_relative_to(target.resolve()):raise SystemExit('Chemin hors préparation')
        dest.parent.mkdir(parents=True,exist_ok=True)
        with t.extractfile(member) as src,dest.open('wb') as out:shutil.copyfileobj(src,out)
        dest.chmod(0o644)
for name in ('Dockerfile','compose.yaml','server/app.py','static/app.js','static/sw.js','static/data/original-art.json','scripts/verify-v23-art-and-salutations.py','tests/test_original_art.py'):
    if not (target/name).is_file():raise SystemExit('Fichier requis absent: '+name)
print('GITHUB_ARCHIVE_STAGED_OK',total,'octets')
PY
log '2/7 — 58 PNG uniques, 73 références, 15 alias, 30 étapes et 183 MP3'
docker run --rm --network none -v "$STAGE/src:/src:ro" -w /src python:3.12-slim python scripts/verify-v23-art-and-salutations.py --root /src || error 'Bibliothèque, audio ou salutations incomplets. Application inchangée.'
docker run --rm --network none -v "$STAGE/src:/src:ro" -w /src python:3.12-slim python scripts/verify-v231-voice.py || error 'Pack Vivienne v5 incomplet. Application inchangée.'
log '3/7 — Tests API et SQLite en base temporaire, syntaxe JavaScript'
docker run --rm --network none -v "$STAGE/src:/src:ro" -w /src -e PYTHONDONTWRITEBYTECODE=1 python:3.12-slim python -m unittest discover -s tests -v || error 'Tests Python en échec. Application inchangée.'
docker run --rm --network none -v "$STAGE/src:/src:ro" -w /src node:22-alpine sh -ec 'node --check static/app.js; node --check static/auth.js; node --check static/sw.js; node --check tests/ui.spec.cjs' || error 'Syntaxe JavaScript invalide. Application inchangée.'
compose config --quiet || error 'Configuration Compose locale invalide'
compose config --services | grep -qx sichosana || error 'Service Compose sichosana absent'
IMAGE=$(docker inspect -f '{{.Config.Image}}' sichosana-app)
OLDID=$(docker inspect -f '{{.Image}}' sichosana-app)
EXPECTED_IMAGE=$(compose config --images sichosana)
[ "$EXPECTED_IMAGE" = "$IMAGE" ] || error 'L’image du service Compose diffère de celle du conteneur courant. Aucun changement.'
MOUNTS=$(docker inspect -f '{{range .Mounts}}{{println .Destination}}{{end}}' sichosana-app)
if printf '%s\n' "$MOUNTS" | grep -Eq '^/app(/|$)'; then error 'Montage de sources /app détecté : mise à jour automatique refusée.'; fi
if [ "$MODE" = --check ]; then log "PRECONTROLE_OK : $REF ; application inchangée."; exit 0; fi
log '4/7 — Construction et recette du candidat dans un conteneur isolé'
docker build -t "$CANDIDATE" "$STAGE/src" || error 'Construction en échec. Application inchangée.'
BUILT=1
verify_container(){
    docker exec -i "$1" python - <<'PY'
import hashlib,json,pathlib,urllib.request
base='http://127.0.0.1:8080'; root=pathlib.Path('/app/static')
def read(path):
    with urllib.request.urlopen(base+path,timeout=6) as r:return r.read()
health=json.loads(read('/api/health'))
assert health.get('version')=='2.3.1',health
art=json.loads(read('/api/v1/media/original-status'))
assert art.get('ready') and art.get('installed')==58 and art.get('expected')==58 and art.get('references')==73 and art.get('shared')==15,art
m=json.loads(read('/data/original-art.json')); aliases=m['aliases']; physical=set(m['files'])-set(aliases)
assert len(physical)==58
for n in sorted(physical):
    path='media/original/'+n+'.png'; b=read('/'+path)
    assert b.startswith(b'\x89PNG\r\n\x1a\n') and hashlib.sha256(b).digest()==hashlib.sha256((root/path).read_bytes()).digest(),n
for name in ('pose_balasana.mp3',):
    req=urllib.request.Request(base+'/voice/vivienne-fr-v5/'+name,headers={'Range':'bytes=0-63'})
    with urllib.request.urlopen(req,timeout=6) as r:assert r.status==206 and len(r.read())==64
print('HEALTH_OK 2.3.1 ; ART_58_73_OK ; AUDIO_RANGE_206_OK')
PY
}
wait_verify(){
    n=0
    while [ "$n" -lt 20 ]; do
        if verify_container "$1" >"$STAGE/last-probe.log" 2>&1; then cat "$STAGE/last-probe.log"; return 0; fi
        n=$((n+1)); sleep 2
    done
    cat "$STAGE/last-probe.log" >&2
    docker logs --tail 40 "$1" >&2 || true
    return 1
}
docker run -d --name "$SMOKE" --network none "$CANDIDATE" >/dev/null || error 'Démarrage isolé impossible.'
SMOKE_STARTED=1
wait_verify "$SMOKE" || error 'Recette isolée en échec. Application inchangée.'
docker rm -f "$SMOKE" >/dev/null; SMOKE_STARTED=0
log '5/7 — Sauvegarde de SQLite et protection de la version actuelle'
mkdir -p "$BASE/backups"; mkdir "$BACKUP"; mkdir "$BACKUP/absent"
cp -p "$APP/.env" "$BACKUP/.env"; cp -p "$APP/compose.yaml" "$BACKUP/compose.yaml"
docker exec -i sichosana-app python - <<'PY'
import datetime,pathlib,sqlite3
src=pathlib.Path('/data/sichosana.sqlite3')
if not src.is_file():raise SystemExit('Base SQLite absente')
folder=src.parent/'backups';folder.mkdir(parents=True,exist_ok=True)
p=folder/('before-v231-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
with sqlite3.connect(str(src)) as a,sqlite3.connect(str(p)) as b:
    a.backup(b)
    if b.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Sauvegarde SQLite invalide')
print('BACKUP_SQLITE_OK',p)
PY
docker tag "$OLDID" "$OLDTAG" || error 'Protection de l’image Docker précédente impossible'
printf '%s\n' "$REF" > "$BACKUP/new-commit.txt"
log '6/7 — Remplacer les seuls fichiers applicatifs et recréer uniquement SichoSana'
for item in $ITEMS; do [ -e "$STAGE/src/$item" ] || error "Fichier de livraison absent : $item"; done
STARTED=1
for item in $ITEMS; do
    if [ -e "$APP/$item" ]; then mv "$APP/$item" "$BACKUP/$item"; else touch "$BACKUP/absent/$item"; fi
    mv "$STAGE/src/$item" "$APP/$item"
done
# La nouvelle image a déjà passé la recette isolée. Le compose et .env locaux restent identiques.
TAGGED=1
docker tag "$CANDIDATE" "$IMAGE"
compose up -d --no-deps --no-build --pull never --force-recreate sichosana || error 'Recréation impossible ; retour arrière automatique.'
log '7/7 — Contrôle du service installé, des 58 PNG et du flux audio HTTP 206'
wait_verify sichosana-app || error 'Recette après déploiement en échec ; retour arrière automatique.'
SUCCESS=1
log "V2.3.1 INSTALLEE — commit $REF"
log "Sauvegarde des fichiers : $BACKUP ; image précédente : $OLDTAG"
log 'Comptes et SQLite conservés. Aucune modification de Forgejo, Cloudflare ou Tailscale.'
log 'Vérifier depuis Safari iPhone/iPad et ordinateur : https://yoga.sicho.cc.cd'
