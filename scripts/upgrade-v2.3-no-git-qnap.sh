#!/bin/sh
# SichoSana V2.3 — mise à jour QNAP sans Git installé.
# Ne touche pas aux autres applications, tunnels Cloudflare, Tailscale ou volume SQLite.
set -eu

APP="/share/CE_CACHEDEV1_DATA/SichoSana/app"
BRANCH="dev/sichosana-20261105"
ARCHIVE="https://codeload.github.com/sicho95/SichoSana/tar.gz/refs/heads/$BRANCH"

[ -d "$APP" ] || { echo "ERREUR : répertoire SichoSana absent : $APP" >&2; exit 1; }
cd "$APP"
command -v docker >/dev/null 2>&1 || { echo "ERREUR : Docker indisponible." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERREUR : Docker Compose indisponible." >&2; exit 1; }
docker inspect sichosana-app >/dev/null 2>&1 || { echo "ERREUR : conteneur sichosana-app absent. Arrêt sans changement." >&2; exit 1; }
[ -f .env ] || { echo "ERREUR : .env local absent. Arrêt sans changement." >&2; exit 1; }
[ -f compose.yaml ] || { echo "ERREUR : compose.yaml absent. Arrêt sans changement." >&2; exit 1; }
# Publier d'abord les 73 PNG sur la branche GitHub dans static/media/original/.
# Ce contrôle est STRICTEMENT ANTÉRIEUR à toute sauvegarde ou copie de sources NAS.
# Aucune archive locale à déposer, aucun Git à installer sur QNAP.
echo "[SichoSana précontrôle] Vérifier les 73 images intégrées dans le même GitHub que le code..."
docker run --rm -i --network bridge -e SICHOSANA_ARCHIVE="$ARCHIVE" \
  python:3.12-slim python - <<'PY'
import io,json,os,pathlib,struct,tarfile,urllib.request,zlib
req=urllib.request.Request(os.environ['SICHOSANA_ARCHIVE'],
                           headers={'User-Agent':'SichoSana-V23-GitHub-media-preflight'})
with urllib.request.urlopen(req,timeout=90) as r:
    data=r.read(150_000_001)
if len(data)>150_000_000:raise SystemExit('Archive GitHub trop volumineuse')
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
    members={}
    for member in tf:
        if not member.isfile():continue
        path=pathlib.PurePosixPath(member.name)
        if len(path.parts)<2:continue
        rel=str(pathlib.PurePosixPath(*path.parts[1:]))
        members[rel]=member
    cfg='static/data/original-art.json'
    if cfg not in members:raise SystemExit('Manifeste original-art.json absent')
    names=json.load(tf.extractfile(members[cfg])).get('files',[])
    if len(names)!=73 or len(set(names))!=73:
        raise SystemExit('Manifeste 73 fichiers non conforme')
    checksums=set()
    for name in names:
        if not isinstance(name,str) or not name.replace('-','').isalnum():
            raise SystemExit('Nom PNG invalide')
        rel='static/media/original/'+name+'.png'
        if rel not in members:raise SystemExit('PNG absent de GitHub : '+rel)
        body=tf.extractfile(members[rel]).read(9_000_001)
        if not 1000<len(body)<=9_000_000 or body[:8]!=b'\x89PNG\r\n\x1a\n':
            raise SystemExit('PNG non conforme : '+rel)
        if body[12:16]!=b'IHDR':
            raise SystemExit('PNG IHDR absent : '+rel)
        w,h=struct.unpack('>II',body[16:24])
        if not(384<=w<=8192 and 384<=h<=8192):
            raise SystemExit('Résolution incorrecte : '+rel)
        # Éliminer les doublons évidents sans accepter 73 copies du même visuel.
        import hashlib
        digest=hashlib.sha256(body).hexdigest()
        if digest in checksums:raise SystemExit('PNG dupliqué : '+rel)
        checksums.add(digest)
print('GITHUB_IMAGES_73_PRECONTROLE_OK ; aucune modification effectuée')
PY

echo "[SichoSana 1/7] Sauvegarde transactionnelle SQLite, comptes compris..."
docker exec -i sichosana-app python - <<'PY'
import datetime, sqlite3
from pathlib import Path
source=Path('/data/sichosana.sqlite3')
if not source.is_file():
    raise SystemExit("Base SQLite introuvable : aucun changement effectué.")
backup=source.parent/'backups'
backup.mkdir(parents=True, exist_ok=True, mode=0o700)
dest=backup/('before-v23-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.sqlite3')
with sqlite3.connect(str(source)) as connection, sqlite3.connect(str(dest)) as target:
    connection.backup(target)
    check=target.execute('PRAGMA integrity_check').fetchone()[0]
    if check!='ok':
        raise SystemExit('Sauvegarde SQLite invalide')
print("BACKUP_SQLITE_OK", dest.name)
PY

echo "[SichoSana 2/7] Télécharger intégralement les sources GitHub dans un conteneur Python isolé..."
# Nécessite que le dépôt GitHub soit public pendant ce téléchargement.
# Le téléchargement est d'abord validé puis les fichiers applicatifs sont remplacés.
# .env, runtime/, .git/ et les fichiers Compose locaux ne sont jamais écrasés.
docker run --rm -i --network bridge -v "$APP:/workspace" -w /workspace \
  -e SICHOSANA_GITHUB_ARCHIVE="$ARCHIVE" python:3.12-slim python - <<'PY'
import os, shutil, tarfile, tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

root=Path('/workspace')
url=os.environ['SICHOSANA_GITHUB_ARCHIVE']
skip_exact={'.env','compose.bridge.yaml','compose.cloudflare.yaml'}
skip_prefix=('runtime/','.data/','.git/','static/media/yoga-api/')
mandatory={'compose.yaml','Dockerfile','server/app.py','static/app.js',
           'scripts/cache-yoga-api-media.py','scripts/upgrade-v2.3-qnap.sh',
           'scripts/upgrade-v2.3-no-git-qnap.sh',
           'static/data/pose-guidance.json','static/voice/vivienne-fr-v2/manifest.json'}
with tempfile.TemporaryDirectory(prefix='sichosana-download-') as d:
    archive=Path(d)/'source.tar.gz'
    req=Request(url,headers={'User-Agent':'SichoSana-QNAP-Upgrade/2.3'})
    try:
        with urlopen(req,timeout=35) as incoming, archive.open('wb') as out:
            if incoming.status!=200:
                raise RuntimeError('Téléchargement GitHub : HTTP '+str(incoming.status))
            shutil.copyfileobj(incoming,out,1024*512)
    except (HTTPError,URLError) as exc:
        raise SystemExit('Téléchargement impossible (dépôt public ?) : '+str(exc))
    print('ARCHIVE_REÇUE_MO',round(archive.stat().st_size/1048576,1))
    if archive.stat().st_size<10000:
        raise SystemExit('Archive GitHub trop petite. Aucun fichier remplacé.')
    with tarfile.open(archive,'r:gz') as tf:
        selected={}
        for member in tf.getmembers():
            if not member.isfile():
                continue
            components=Path(member.name).parts
            if len(components)<2 or any(x in ('..','') for x in components):
                raise SystemExit('Chemin suspect dans archive GitHub.')
            relative=Path(*components[1:]).as_posix()
            if relative.startswith('/') or relative in skip_exact or relative.startswith(skip_prefix):
                continue
            if member.size>30_000_000:
                raise SystemExit('Fichier source anormalement volumineux : '+relative)
            selected[relative]=member
        missing=mandatory-selected.keys()
        if missing:
            raise SystemExit('Archive incomplète : '+', '.join(sorted(missing)))
        # Contrôle de version sur une source clé avant toute écriture.
        app_py=tf.extractfile(selected['server/app.py']).read()
        if b'"version": "2.3.0"' not in app_py:
            raise SystemExit('Version incorrecte : attendue 2.3.0. Aucun fichier remplacé.')
        count=0
        for rel,member in selected.items():
            target=root/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(prefix='.sichosana-new-',dir=str(target.parent))
            try:
                with os.fdopen(fd,'wb') as out,tf.extractfile(member) as inp:
                    shutil.copyfileobj(inp,out)
                os.chmod(tmp,0o644)
                os.replace(tmp,target)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
            count+=1
    print('SOURCES_MISES_A_JOUR_OK',count,'fichiers')
PY

echo "[SichoSana 3/7] Import privé des PNG Yoga API (aucun envoi vers GitHub)..."
docker run --rm --network bridge -v "$APP:/workspace" -w /workspace \
  python:3.12-slim python scripts/cache-yoga-api-media.py

echo "[SichoSana 4/7] Préserver .env et maintenir la route IP NAS 192.168.1.69:18887..."
cp -p .env ".env.bak.$(date +%Y%m%d%H%M%S)"
if grep -q '^SICHOSANA_BIND=' .env; then
  sed -i 's/^SICHOSANA_BIND=.*/SICHOSANA_BIND=192.168.1.69/' .env
else
  printf '\nSICHOSANA_BIND=192.168.1.69\n' >> .env
fi
if grep -q '^SICHOSANA_PORT=' .env; then
  sed -i 's/^SICHOSANA_PORT=.*/SICHOSANA_PORT=18887/' .env
else
  printf 'SICHOSANA_PORT=18887\n' >> .env
fi
chmod 600 .env

echo "[SichoSana 5/7] Vérifier les 183 MP3 et le compose avant redémarrage..."
docker run --rm -i --network bridge -v "$APP:/workspace:ro" -w /workspace \
  python:3.12-slim python - <<'PY'
import json
from pathlib import Path
pack=Path('static/voice/vivienne-fr-v2')
manifest=json.loads((pack/'manifest.json').read_text())
assert manifest['voiceId']=='fr-FR-VivienneMultilingualNeural', 'Mauvaise identité vocale'
assert len(manifest['files'])>=183, 'Fichiers vocaux manquants'
missing=[x['src'] for x in manifest['files'].values() if not (pack/x['src']).is_file()]
if missing:
    raise SystemExit('MP3 manquants : '+str(missing[:6]))
salutations=json.loads(Path('static/data/salutations.json').read_text())
required=['salutation_'+r['id']+'_'+str(i).zfill(2)+'_'+mode
    for r in salutations['routines'] for i,_ in enumerate(r['steps'])
    for mode in ('full','easy')]
missing_salutes=[k for k in required if k not in manifest['files'] or not (pack/manifest['files'][k]['src']).is_file()]
if missing_salutes:
    raise SystemExit('DÉPLOIEMENT V2.3 BLOQUÉ : '
      +str(len(missing_salutes))+' MP3 des salutations absents. '
      +'Le moteur Edge TTS doit produire tous les clips avant mise en production.')
print("PACK_VIVIENNE_OK",len(manifest['files']),'MP3 et 60 consignes de salutations vérifiées')
PY
echo "[SichoSana 5b/7] 73 PNG récupérés automatiquement dans les sources GitHub ; aucun ZIP NAS requis."
docker compose -f compose.yaml -p sichosana config --quiet

echo "[SichoSana 6/7] Conserver l'image antérieure et recréer SichoSana uniquement..."
STAMP="$(date +%Y%m%d%H%M%S)"
docker image inspect sichosana:local >/dev/null 2>&1 && \
  docker tag sichosana:local "sichosana:backup-$STAMP" || true
docker compose -f compose.yaml -p sichosana up -d --build --no-deps --force-recreate

echo "[SichoSana 7/7] Contrôles service et port LAN..."
RESPONSE=''
i=0
while [ "$i" -lt 20 ]; do
  if RESPONSE="$(curl -fsS --max-time 5 http://192.168.1.69:18887/api/health 2>/dev/null)" ; then
    break
  fi
  i=$((i+1))
  sleep 2
done
printf '%s\n' "$RESPONSE"
case "$RESPONSE" in
  *'"version": "2.3.0"'*) ;;
  *) echo "ATTENTION : API V2.3 non confirmée. Consulter docker logs --tail 80 sichosana-app" >&2; exit 1;;
esac
docker inspect sichosana-app --format 'RÉSEAU={{.HostConfig.NetworkMode}} | STATUT={{.State.Status}}'
echo "[SichoSana] Vérification de la bibliothèque originale complète et des MP3 HTTP Range..."
ART_STATUS="$(curl -fsS --max-time 10 http://192.168.1.69:18887/api/v1/media/original-status)"
printf '%s\\n' "$ART_STATUS"
case "$ART_STATUS" in
  *'"ready": true'*'"installed": 73'*) ;;
  *) echo "ERREUR : les 73 PNG ne sont pas servis. Vérifier les volumes et la reconstruction." >&2; exit 1;;
esac
AUDIO_HTTP="$(curl -sS --max-time 12 -o /dev/null -w '%{http_code}' -H 'Range: bytes=0-63' http://192.168.1.69:18887/voice/vivienne-fr-v2/pose_balasana.mp3)"
[ "$AUDIO_HTTP" = "206" ] || { echo "ERREUR : MP3 Range devrait répondre 206, reçu $AUDIO_HTTP" >&2; exit 1; }
echo "MP3_RANGE_OK HTTP 206"
echo "[SichoSana] TERMINÉ : comptes conservés, autres conteneurs, DNS et tunnel inchangés."
echo "[SichoSana] Ouvrir : https://yoga.sicho.cc.cd"
echo "[SichoSana] SMTP SichoBooks : sh scripts/configure-smtp-from-sichobooks-qnap.sh"
