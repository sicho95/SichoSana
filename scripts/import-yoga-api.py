#!/usr/bin/env python3
"""Import ponctuel Yoga API vers SQLite, aucune dépendance en usage normal.
Images : provenance et crédit Flaticon conservés. Ne pas générer d'images par IA à partir de ces assets.
"""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

API = "https://yoga-api-nzy4.onrender.com/v1/poses"
VALID_LEVELS = {"beginner": "Débutant", "intermediate": "Intermédiaire", "expert": "Avancé"}
CREDITS = {
    "green": "Yoga icons created by dDara - Flaticon",
    "pink": "Easy icons created by monkik - Flaticon",
    "red": "CC0 (domaine public)",
    "unknown": "Licence à vérifier avant reproduction"
}

def normalize(row):
    if not isinstance(row, dict) or not isinstance(row.get("id"), (str, int)):
        raise ValueError("Posture invalide")
    ref = str(row["id"])
    level = str(row.get("difficulty_level", "")).lower()
    png = str(row.get("url_png", ""))
    # L'import n'enregistre que l'URL source. La PWA ne télécharge rien à l'exécution.
    return {
        "id": "yoga-api-" + ref,
        "nom": str(row.get("english_name") or row.get("sanskrit_name") or ref)[:100],
        "sanskrit": str(row.get("sanskrit_name") or "")[:150],
        "niveau": VALID_LEVELS.get(level, "Non classé"),
        "focus": str(row.get("category_name") or "Yoga")[:90],
        "instructions": str(row.get("pose_description") or "Consulter une instruction de pratique validée.")[:1500],
        "prudence": "Adapter la posture au confort personnel. En cas de douleur, interrompre la pratique.",
        "source": "alexcumplido/yoga-api",
        "originalId": ref,
        "imageSource": png if png.startswith("https://res.cloudinary.com/dko1be2jy/") else None,
        "imageLocal": None,
        "assetLicense": "unknown"
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", type=Path, help="Fichier JSON téléchargé de Yoga API (import hors ligne).")
    p.add_argument("--database", type=Path, default=Path("runtime/sichosana.sqlite3"))
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.snapshot:
        raw = a.snapshot.read_bytes()
    else:
        with urlopen(API, timeout=25) as response:
            raw = response.read(3_000_000)
    source = json.loads(raw)
    if not isinstance(source, list):
        raise ValueError("Yoga API devrait retourner une liste de postures.")
    normalized = [normalize(row) for row in source]
    if len(normalized) < 10:
        raise ValueError("Import suspect : moins de dix postures.")
    print("Postures prêtes :", len(normalized), "— mode", "simulation" if a.dry_run else "import")
    if a.dry_run:
        return
    if not a.database.exists():
        raise FileNotFoundError("La base doit d'abord être initialisée par le serveur : " + str(a.database))
    with sqlite3.connect(a.database) as c:
        if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='poses'").fetchone():
            raise RuntimeError("Table poses inexistante, vérifier le chemin SQLite.")
        for item in normalized:
            c.execute(
                "INSERT INTO poses (id,data,origin,asset_license,imported_at) VALUES(?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET data=excluded.data,asset_license=excluded.asset_license,imported_at=excluded.imported_at",
                (item["id"], json.dumps(item, ensure_ascii=False), "yoga-api", CREDITS["unknown"], int(datetime.now(timezone.utc).timestamp()))
            )
    print("Import terminé. Les illustrations ne sont PAS copiées : droits à qualifier et attribution requise.")

if __name__ == "__main__":
    main()
