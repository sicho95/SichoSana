#!/bin/sh
# Import contrôlé des PNG originaux de SichoSana depuis une archive
# déposée manuellement dans File Station, sans toucher au SMTP, aux comptes,
# au réseau bridge, à Cloudflare ni aux autres conteneurs.
set -eu
APP="/share/CE_CACHEDEV1_DATA/SichoSana/app"
ZIP="${1:-}"
if [ -z "$ZIP" ] || [ ! -f "$ZIP" ]; then
 echo "Usage : sh scripts/install-original-art-qnap.sh /chemin/vers/SichoSana_illustrations_originales_salutations_v23.zip" >&2
 exit 2
fi
[ -d "$APP" ] && [ -f "$APP/compose.yaml" ] && [ -f "$APP/.env" ] || {
 echo "Répertoire SichoSana non prêt : aucune modification." >&2;exit 1;
}
cd "$APP"
BUNDLE="$(cd "$(dirname "$ZIP")" && pwd)/$(basename "$ZIP")"
echo "[SichoSana ART 1/3] Vérification des 73 PNG et de leurs empreintes SHA-256..."
docker run --rm -i --network none -v "$APP:/workspace" -v "$BUNDLE:/tmp/originals.zip:ro" \
 -w /workspace python:3.12-slim python - <<'PY'
import hashlib, json, os, pathlib, tempfile, zipfile
root=pathlib.Path('/workspace/static/media/original')
root.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile('/tmp/originals.zip') as archive:
    data=json.loads(archive.read('artwork-manifest.json'))
    files=data['files']
    if len(files)!=73 or data['catalog48']['present']!=48 or data['essential13']['present']!=13 or data['salutationExtras']['present']!=12:
        raise SystemExit('Manifeste incomplet ou nombre de fichiers inattendu : aucune copie.')
    if data.get('missing'):
        raise SystemExit('Nombre d’illustrations encore manquantes incohérent.')
    for name,info in files.items():
        rel='media/original/'+name+'.png'
        if info['path']!='/'+rel or name.startswith('.') or '/' in name or '\\' in name:
            raise SystemExit('Chemin PNG invalide')
        item=archive.getinfo(rel)
        if item.file_size>9_000_000:
            raise SystemExit('PNG trop lourd.')
        body=archive.read(rel)
        if len(body)<1000 or body[:8]!=b'\x89PNG\r\n\x1a\n':
            raise SystemExit('Fichier non PNG')
        if hashlib.sha256(body).hexdigest()!=info['sha256']:
            raise SystemExit('Contrôle SHA échoué : '+name)
    for name,info in files.items():
        body=archive.read('media/original/'+name+'.png')
        target=root/(name+'.png')
        fd,tmp=tempfile.mkstemp(prefix='.sichosana-png-',dir=str(root))
        try:
            with os.fdopen(fd,'wb') as f:f.write(body)
            os.chmod(tmp,0o644)
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
print('ORIGINAL_ART_OK',len(files),'PNG installés ; 0 illustration manquante.')
PY
echo "[SichoSana ART 2/3] Reconstruire uniquement l'application SichoSana..."
docker compose -f compose.yaml -p sichosana up -d --build --no-deps --force-recreate
echo "[SichoSana ART 3/3] Contrôle API..."
curl -fsS --max-time 10 http://192.168.1.69:18887/api/health || exit 1
echo
echo "[SichoSana] Images intégrées sans modifier SQLite, Cloudflare ou les autres services."
