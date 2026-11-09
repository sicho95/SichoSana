#!/usr/bin/env python3
"""Audit bloquant SichoSana V2.3 : 73 fiches / 58 PNG uniques et 30 étapes guidées.
Sans dépendance externe. Ne modifie jamais les fichiers ni la base.
Les vérifications techniques ne constituent pas une certification anatomique.
"""
import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
import zipfile
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

def check(condition, message):
    if not condition:
        raise ValueError(message)

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify_png(data, name):
    check(data.startswith(PNG_SIGNATURE), f"{name}: signature PNG invalide")
    check(len(data) >= 1000, f"{name}: PNG trop petit")
    pos = 8
    dimensions = None
    has_image = False
    finished = False
    while pos + 12 <= len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        check(size <= 16_000_000 and pos + 12 + size <= len(data),
              f"{name}: structure PNG tronquée")
        body = data[pos + 8:pos + 8 + size]
        stored = struct.unpack(">I", data[pos + 8 + size:pos + 12 + size])[0]
        actual = zlib.crc32(kind + body) & 0xffffffff
        check(stored == actual, f"{name}: CRC PNG incorrect")
        if kind == b"IHDR":
            check(dimensions is None and size == 13, f"{name}: IHDR invalide")
            w, h, depth, color, *_ = struct.unpack(">IIBBBBB", body)
            check(384 <= w <= 8192 and 384 <= h <= 8192 and depth == 8
                  and color in (2, 6), f"{name}: résolution / format inattendu ({w}x{h})")
            dimensions = (w, h)
        if kind == b"IDAT":
            has_image = True
        pos += 12 + size
        if kind == b"IEND":
            finished = True
            break
    check(dimensions is not None and has_image and finished and pos == len(data),
          f"{name}: PNG incomplet ou données supplémentaires")
    return dimensions

def audit(root, artwork=None, metadata_only=False):
    data = root / "static" / "data"
    yoga = load(data / "yoga.json")
    api = load(data / "yoga-api-library.json")
    salut = load(data / "salutations.json")
    art = load(data / "original-art.json")
    essentials = {p["id"] for p in yoga["poses"]}
    catalog = {p["id"] for p in api["poses"]}
    extras = {p["id"] for p in salut["extraPoses"]}
    check(len(essentials) == 13 and len(catalog) == 48 and len(extras) == 12,
          "Catalogue différent de 13 + 48 + 12")
    expected = essentials | catalog | extras
    check(len(expected) == 73, "Identifiants du catalogue non disjoints")
    listed = art.get("files")
    check(isinstance(listed, list) and len(listed) == 73 and set(listed) == expected
          and len(set(listed)) == 73, "original-art.json: 73 correspondances exactes non garanties")
    aliases = art.get("aliases", {})
    check(isinstance(aliases, dict) and len(aliases) == 15,
          "15 références partagées attendues")
    check(all(a in expected and b in expected and a != b and b not in aliases
              for a, b in aliases.items()),
          "Alias d'illustration invalide, cyclique ou dirigé vers un autre alias")
    physical = expected - set(aliases)
    check(len(physical) == 58 and art.get("expectedPhysicalFiles") == 58,
          "58 PNG physiques canoniques attendus")
    all_poses = {p["id"] for p in yoga["poses"] + api["poses"] + salut["extraPoses"]}
    routines = {r["id"]: r for r in salut["routines"]}
    check(set(routines) == {"salutation-soleil", "salutation-lune"},
          "Deux salutations attendues")
    sun, moon = routines["salutation-soleil"], routines["salutation-lune"]
    check(len(sun["steps"]) == 12 and len(moon["steps"]) == 18,
          "Le Soleil doit avoir 12 étapes et la Lune 18")
    check(sun["steps"][6]["poseId"] == "urdhva-mukha"
          and sun["steps"][6]["easyPoseId"] == "bhujangasana",
          "Erreur chien tête en haut / cobra à l'étape 7")
    check(sun["steps"][5]["poseId"] == "chaturanga"
          and sun["steps"][5]["easyPoseId"] == "phalakasana",
          "Variante douce Chaturanga incorrecte")
    check(len(sun["fullPrerequisites"]) == 8 and len(sun["easyPrerequisites"]) == 7
          and len(moon["fullPrerequisites"]) == 8, "Prérequis incomplets")
    manifest = load(root / "static" / "voice" / "vivienne-fr-v2" / "manifest.json")
    clips = manifest["files"]
    check(manifest.get("voiceId") == "fr-FR-VivienneMultilingualNeural"
          and len(clips) == 183, "Pack vocal V2 attendu : 183 clips avec la voix ResurGo")
    for r in routines.values():
        possible = {s["poseId"] for s in r["steps"]}
        easy = {s.get("easyPoseId", s["poseId"]) for s in r["steps"]}
        check(all(x in all_poses for x in possible | easy), f"{r['id']}: posture inconnue")
        check(set(r["fullPrerequisites"]) == possible and
              set(r["easyPrerequisites"]) == easy, f"{r['id']}: prérequis non alignés")
        for i, step in enumerate(r["steps"]):
            check(step.get("breath") in ("inspiration", "expiration", "maintien"),
                  f"{r['id']} étape {i + 1}: respiration absente")
            check(isinstance(step.get("cue"), str) and len(step["cue"]) >= 15,
                  f"{r['id']} étape {i + 1}: instruction absente")
            for mode in ("full", "easy"):
                key = f"salutation_{r['id']}_{i:02d}_{mode}"
                check(key in clips, f"Consigne vocale absente : {key}")
    salutation_clip_keys = [k for k in clips if k.startswith("salutation_")]
    check(len(salutation_clip_keys) == 60, "60 clips Soleil/Lune attendus")
    missing_audio = []
    for entry in clips.values():
        rel = entry.get("src", "")
        check(re.fullmatch(r"[a-zA-Z0-9_.-]+\.mp3", rel) is not None,
              "Chemin audio non sécurisé")
        path = root / "static" / "voice" / "vivienne-fr-v2" / rel
        if not path.is_file() or path.stat().st_size < 256:
            missing_audio.append(rel)
    check(not missing_audio, f"MP3 absents/incomplets : {missing_audio[:8]}")
    print("GUIDAGE_OK 12 étapes Soleil + 18 étapes Lune, prérequis 8/7/8, 60 clips, 183 MP3.")
    if metadata_only:
        print("METADATA_OK 73 fiches / 58 références PNG canoniques ; binaires NON vérifiés.")
        return
    zip_path = pathlib.Path(artwork) if artwork else None
    physical_hashes = {}
    if zip_path:
        check(zip_path.is_file(), "Archive d'illustrations introuvable")
        with zipfile.ZipFile(zip_path) as archive:
            check(archive.testzip() is None, "Archive ZIP corrompue")
            zip_manifest = json.loads(archive.read("artwork-manifest.json"))
            files = zip_manifest.get("files", {})
            check(isinstance(files, dict) and set(files) == expected,
                  "ZIP : identifiants manquants ou étrangers")
            archive_hashes = {}
            for name in sorted(expected):
                rel = f"media/original/{name}.png"
                check(files[name].get("path") == "/" + rel,
                      f"ZIP : mauvaise correspondance {name}")
                blob = archive.read(rel)
                digest = hashlib.sha256(blob).hexdigest()
                check(digest == files[name].get("sha256"),
                      f"ZIP : SHA-256 incorrect pour {name}")
                verify_png(blob, name)
                archive_hashes[name] = digest
            for alias, target in aliases.items():
                check(archive_hashes[alias] == archive_hashes[target],
                      f"Alias différent de sa posture canonique : {alias} / {target}")
            for name in physical:
                digest = archive_hashes[name]
                check(digest not in physical_hashes,
                      f"Deux illustrations physiques identiques : {name}")
                physical_hashes[digest] = name
    else:
        folder = root / "static" / "media" / "original"
        check(folder.is_dir(), "Bibliothèque PNG GitHub absente")
        for name in sorted(physical):
            p = folder / (name + ".png")
            check(p.is_file(), f"Illustration manquante : {name}")
            blob = p.read_bytes()
            verify_png(blob, name)
            digest = hashlib.sha256(blob).hexdigest()
            check(digest not in physical_hashes,
                  f"Deux illustrations physiques identiques : {name}")
            physical_hashes[digest] = name
        unexpected = {p.stem for p in folder.glob("*.png")} - physical
        check(not unexpected, f"PNG superflus / alias dupliqués : {sorted(unexpected)[:10]}")
    check(len(physical_hashes) == 58, "58 illustrations uniques attendues")
    print("ORIGINAL_ART_OK 73 fiches, 58 PNG canoniques distincts, 15 alias partagés, CRC/format contrôlés.")
    print("L'anatomie et les variantes gauche/droite exigent toujours une revue visuelle.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--artwork")
    ap.add_argument("--metadata-only", action="store_true")
    opts = ap.parse_args()
    try:
        audit(pathlib.Path(opts.root).resolve(), opts.artwork, opts.metadata_only)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as e:
        print("VERIFICATION_ECHOUEE:", e, file=sys.stderr)
        raise SystemExit(1)
