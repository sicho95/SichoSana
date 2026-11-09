#!/usr/bin/env python3
"""Publier 58 PNG canoniques pour 73 fiches yoga dans GitHub sans Git local.

Usage :
  GITHUB_TOKEN=... python3 scripts/publish-v23-original-art-github.py \
      /chemin/SichoSana_V2.3_73_illustrations_originales.zip

Le ZIP doit être disponible localement : aucune connexion à la bibliothèque
ChatGPT n'est présumée. Upload des blobs un par un, puis UN SEUL commit atomique.
Ne modifie ni Forgejo, ni QNAP, ni SQLite.
"""
import base64
import hashlib
import json
import os
import pathlib
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib

REPO = "sicho95/SichoSana"
BRANCH = "dev/sichosana-20261105"
API = "https://api.github.com/repos/" + REPO
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
USER_AGENT = "SichoSana-v23-58-unique-images-publisher"
MAX_PNG = 9_000_000


def fail(message):
    raise SystemExit("PUBLICATION_BLOQUEE: " + message)


def request(method, path, payload=None):
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
            **({"Content-Type": "application/json"} if payload is not None else {}),
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace")
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            fail(f"GitHub API HTTP {exc.code} {path}: {detail}")
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            fail(f"GitHub API indisponible : {exc}")
    fail("Échecs HTTP répétés")


def verify_png(content, name):
    if len(content) < 1_000 or len(content) > MAX_PNG:
        fail(f"{name}: taille PNG anormale")
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"{name}: mauvais format")
    position = 8
    seen_header = seen_data = finished = False
    while position + 12 <= len(content):
        n = struct.unpack(">I", content[position:position + 4])[0]
        kind = content[position + 4:position + 8]
        end = position + 12 + n
        if n > MAX_PNG or end > len(content):
            fail(f"{name}: PNG tronqué")
        payload = content[position + 8:position + 8 + n]
        crc = struct.unpack(">I", content[end - 4:end])[0]
        if (zlib.crc32(kind + payload) & 0xffffffff) != crc:
            fail(f"{name}: erreur CRC")
        if kind == b"IHDR":
            if seen_header or n != 13:
                fail(f"{name}: en-tête PNG invalide")
            w, h = struct.unpack(">II", payload[:8])
            if not (384 <= w <= 8192 and 384 <= h <= 8192):
                fail(f"{name}: dimensions incorrectes ({w}x{h})")
            seen_header = True
        if kind == b"IDAT":
            seen_data = True
        position = end
        if kind == b"IEND":
            finished = True
            break
    if not (seen_header and seen_data and finished and position == len(content)):
        fail(f"{name}: PNG incomplet")


def main(archive_name):
    if not TOKEN:
        fail("Variable d'environnement GITHUB_TOKEN absente")
    archive_path = pathlib.Path(archive_name)
    if not archive_path.is_file():
        fail(f"Archive introuvable : {archive_path}")
    branch_ref = urllib.parse.quote(BRANCH, safe="/")
    manifest_response = request("GET", "/contents/static/data/original-art.json?ref=" + urllib.parse.quote(BRANCH, safe=""))
    if manifest_response.get("encoding") != "base64":
        fail("Manifeste GitHub inaccessible")
    manifest = json.loads(base64.b64decode(manifest_response["content"]))
    ids = manifest.get("files", [])
    if not isinstance(ids, list) or len(ids) != 73 or len(set(ids)) != 73:
        fail("Manifeste GitHub: 73 identifiants uniques attendus")
    if any(not isinstance(x, str) or not re.fullmatch(r"[a-z0-9-]+", x) for x in ids):
        fail("Identifiants de fichiers suspects")
    aliases = manifest.get("aliases", {})
    if not isinstance(aliases, dict) or len(aliases) != 15:
        fail("Le manifeste GitHub doit déclarer exactement 15 alias")
    if any(key not in ids or target not in ids or key == target or target in aliases
           for key, target in aliases.items()):
        fail("Correspondance d'alias invalide ou cyclique")
    canonical = sorted(set(ids) - set(aliases))
    if len(canonical) != 58 or manifest.get("expectedPhysicalFiles") != 58:
        fail("58 illustrations canoniques attendues")
    pictures = {}
    sha_by_name = {}
    with zipfile.ZipFile(archive_path) as z:
        if z.testzip() is not None:
            fail("Archive ZIP corrompue")
        artwork_manifest = json.loads(z.read("artwork-manifest.json"))
        files = artwork_manifest.get("files", {})
        if not isinstance(files, dict) or set(files) != set(ids):
            fail("Les 73 noms du ZIP ne correspondent pas aux fiches GitHub")
        if any(artwork_manifest.get(k, {}).get("present") != count for k, count in
               (("catalog48", 48), ("essential13", 13), ("salutationExtras", 12))):
            fail("Compte des groupes d'illustrations incorrect")
        for name in sorted(ids):
            expected = "media/original/" + name + ".png"
            entry = files[name]
            if entry.get("path") != "/" + expected:
                fail(name + ": chemin du manifeste incohérent")
            try:
                blob = z.read(expected)
            except KeyError:
                fail(name + ": fichier PNG absent du ZIP")
            verify_png(blob, name)
            digest = hashlib.sha256(blob).hexdigest()
            if digest != entry.get("sha256"):
                fail(name + ": empreinte SHA-256 du ZIP incorrecte")
            sha_by_name[name] = digest
            if name in canonical:
                pictures[name] = blob
    for name, target in aliases.items():
        if sha_by_name[name] != sha_by_name[target]:
            fail(name + ": correspondance différente de la posture partagée " + target)
    if len({sha_by_name[name] for name in canonical}) != 58:
        fail("Plusieurs des 58 dessins canoniques sont identiques")
    print("VERIFICATION_LOCALE_OK: 73 fiches, 58 dessins distincts et 15 alias exacts.")

    head = request("GET", "/git/ref/heads/" + branch_ref)["object"]["sha"]
    base_tree = request("GET", "/git/commits/" + head)["tree"]["sha"]
    tree_elements = []
    for i, name in enumerate(canonical, 1):
        blob = pictures[name]
        uploaded = request("POST", "/git/blobs", {
            "content": base64.b64encode(blob).decode("ascii"),
            "encoding": "base64",
        })
        if not re.fullmatch(r"[a-f0-9]{40}", uploaded.get("sha", "")):
            fail(f"GitHub n'a pas confirmé l'image {name}")
        tree_elements.append({
            "path": "static/media/original/" + name + ".png",
            "mode": "100644",
            "type": "blob",
            "sha": uploaded["sha"],
        })
        print(f"IMAGE_{i:02d}/58_UPLOAD_OK {name}.png")

    # Un seul commit : aucune livraison partielle des 58 illustrations.
    current = request("GET", "/git/ref/heads/" + branch_ref)["object"]["sha"]
    if current != head:
        fail("Branche modifiée pendant l'envoi, aucun commit publié; recommencer")
    tree = request("POST", "/git/trees", {
        "base_tree": base_tree,
        "tree": tree_elements,
    })["sha"]
    commit = request("POST", "/git/commits", {
        "message": "assets(v2.3): publish 58 canonical yoga PNGs with 15 aliases for 73 poses",
        "tree": tree,
        "parents": [head],
    })["sha"]
    request("PATCH", "/git/refs/heads/" + branch_ref, {
        "sha": commit,
        "force": False,
    })
    remote = request("GET", "/git/trees/" + tree + "?recursive=1")
    expected = {x["path"]: x["sha"] for x in tree_elements}
    actual = {x["path"]: x["sha"] for x in remote.get("tree", []) if x.get("type") == "blob"}
    if remote.get("truncated"):
        fail("GitHub n'a pas renvoyé l'arbre complet")
    missing = [name for name, sha in expected.items() if actual.get(name) != sha]
    if missing:
        fail(f"Contrôle après commit échoué ({len(missing)} images)")
    final_ref = request("GET", "/git/ref/heads/" + branch_ref)["object"]["sha"]
    if final_ref != commit:
        fail("La branche a changé juste après la publication")
    print("GITHUB_58_IMAGES_73_POSES_OK", commit)
    print(f"https://github.com/{REPO}/tree/{BRANCH}/static/media/original")
    print("Note : contrôle visuel des postures toujours requis.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("Usage : GITHUB_TOKEN=... python3 publish-v23-original-art-github.py /chemin/73-images.zip")
    try:
        main(sys.argv[1])
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        fail(str(error))
