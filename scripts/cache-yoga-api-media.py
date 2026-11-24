#!/usr/bin/env python3
"""Cache local des PNG officiels référencés dans le snapshot Yoga API.

Usage NAS : exécuter avant docker compose build, jamais pendant la séance.
Le dépôt GitHub ne publie pas les fichiers Flaticon ; ceux-ci sont récupérés
seulement pour l'instance SichoSana. Le client indique les crédits Flaticon.
"""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE = Path("static/data/yoga-api-library.json")
DEST = Path("static/media/yoga-api")
ALLOWED = re.compile(r"^https://res\.cloudinary\.com/dko1be2jy/image/upload/[a-zA-Z0-9_/,.-]+/yoga-api/[a-zA-Z0-9_-]+\.png$")
MAX_BYTES = 5_000_000
PNG_MAGIC = bytes([137, 80, 78, 71, 13, 10, 26, 10])


def download(pose):
    ident = pose["id"]
    src = pose.get("imageSource")
    if not re.fullmatch(r"yoga-api-[0-9]{1,3}", ident) or not isinstance(src,str) or not ALLOWED.fullmatch(src):
        return ident, "source non autorisée"
    file = DEST / (ident + ".png")
    if file.exists() and file.stat().st_size > 2_000:
        with file.open("rb") as stream:
            if stream.read(8) == PNG_MAGIC:
                return ident, None
    req = Request(src, headers={"User-Agent": "SichoSana/2.2 (+https://yoga.sicho.cc.cd)"})
    try:
        with urlopen(req, timeout=24) as response:
            if response.status != 200 or "image" not in response.headers.get("Content-Type", ""):
                raise ValueError("Réponse non image")
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES or len(raw) < 2_000 or not raw.startswith(PNG_MAGIC):
            raise ValueError("PNG invalide ou trop volumineux")
        tmp = DEST / (ident + ".download")
        tmp.write_bytes(raw)
        tmp.replace(file)
        return ident, None
    except (OSError, ValueError) as exc:
        return ident, type(exc).__name__


def main():
    catalog = json.loads(SOURCE.read_text(encoding="utf-8"))
    poses = catalog["poses"]
    DEST.mkdir(parents=True, exist_ok=True)
    errors=[]
    with ThreadPoolExecutor(max_workers=5) as executor:
        for future in as_completed([executor.submit(download, p) for p in poses]):
            ident, err = future.result()
            if err:
                errors.append((ident,err))
    ready = sorted(p["id"] for p in poses if (DEST/(p["id"]+".png")).is_file())
    print("YOGA_API_PNG_LOCAL", len(ready),"/",len(poses))
    if errors:
        print("Images manquantes :", ", ".join(i+":"+e for i,e in errors))
    if not ready:
        raise SystemExit("Aucune image Yoga API téléchargée : conserver l'installation précédente.")
    manifest = {
      "source": "https://github.com/alexcumplido/yoga-api",
      "assetsOrigin": "https://res.cloudinary.com/dko1be2jy/",
      "licenseNote": "Les styles rose et vert sont issus de Flaticon et exigent crédit. Les images rouges sont CC0.",
      "files": {ident: {"src": "/media/yoga-api/"+ident+".png",
                         "sha256": hashlib.sha256((DEST/(ident+".png")).read_bytes()).hexdigest()}
                for ident in ready}
    }
    (DEST/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
