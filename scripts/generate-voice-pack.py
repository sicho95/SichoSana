#!/usr/bin/env python3
"""Pré-génère les voix SichoSana avec l'identité Vivienne de ResurGo Running."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path

VOICE = "fr-FR-VivienneMultilingualNeural"
RATE, PITCH, VOLUME = "-12%", "-1Hz", "+0%"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def clips(catalog, yoga):
    found = []
    for session in catalog["sessions"]:
        for level in ("discrete", "equilibree", "enveloppante"):
            for index, item in enumerate(session["scripts"][level]):
                text = item.get("text", "").strip()
                if text:
                    key = session["id"] + "_" + level + "_" + str(index).zfill(2)
                    if len(text) > 1200 or not all(x.isalnum() or x in "_-" for x in key):
                        raise ValueError("Segment audio invalide : " + key)
                    found.append((key, text))
    # Même identité Vivienne pour les consignes de yoga et les méditations.
    for pose in yoga.get("poses", []):
        text = (pose.get("nom", "") + ". " + pose.get("instructions", "") + " " + pose.get("prudence", "")).strip()
        found.append(("pose_" + pose["id"], text))
    if len(set(k for k, _ in found)) != len(found):
        raise ValueError("Segments vocaux en doublon")
    return found

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("static/data/meditations.json"))
    parser.add_argument("--out", type=Path, default=Path("static/voice/vivienne-fr-v1"))
    parser.add_argument("--yoga", type=Path, default=Path("static/data/yoga.json"))
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    from edge_tts import Communicate
    source = json.loads(args.catalog.read_text(encoding="utf-8"))
    yoga = json.loads(args.yoga.read_text(encoding="utf-8"))
    dest = args.out
    dest.mkdir(parents=True, exist_ok=True)
    lock = asyncio.Semaphore(min(max(args.jobs, 1), 4))
    entries = {}

    async def render(key, text):
        target = dest / (key + ".mp3")
        async with lock:
            for attempt in range(4):
                try:
                    if not target.exists() or target.stat().st_size < 2000:
                        await Communicate(text=text, voice=VOICE, rate=RATE, pitch=PITCH, volume=VOLUME).save(str(target))
                    if target.stat().st_size < 2000:
                        raise ValueError("Fichier audio vide : " + key)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(1 + attempt)
        entries[key] = {
            "src": target.name, "sha256": sha(target),
            "bytes": target.stat().st_size, 
            "textSha256": hashlib.sha256(text.encode("utf-8")).hexdigest()
        }

    await asyncio.gather(*(render(k, t) for k, t in clips(source, yoga)))
    manifest = {
        "format": "sichosana-voice-pack", "packId": "vivienne-fr-v1",
        "locale": "fr-FR", "voiceId": VOICE, "rate": RATE,
        "pitch": PITCH, "volume": VOLUME,
        "sourceIdentity": "ResurGo_Fitness Running female coach v2",
        "status": "candidate-awaiting-damien-audition",
        "catalogSha256": sha(args.catalog), "yogaCatalogSha256": sha(args.yoga),
        "files": dict(sorted(entries.items()))
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(entries), "segments audio générés")

if __name__ == "__main__":
    asyncio.run(main())
