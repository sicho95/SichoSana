"""Sauvegarde cohérente SQLite via l'API backup, sans arrêt du service."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3

def backup(source: Path, dest: Path):
    if not source.is_file():
        raise FileNotFoundError(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source}?mode=ro",uri=True) as src, sqlite3.connect(dest) as dst:
        src.backup(dst)
        result=dst.execute("PRAGMA integrity_check").fetchone()[0]
        if result!="ok":
            dest.unlink(missing_ok=True)
            raise RuntimeError("Sauvegarde corrompue : "+result)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path(os.environ.get("SICHOSANA_DATA_DIR","runtime"))/"sichosana.sqlite3")
    parser.add_argument("--dest",type=Path,default=Path("backups")/("sichosana-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")+".sqlite3"))
    a=parser.parse_args()
    backup(a.source,a.dest)
    print(a.dest)
