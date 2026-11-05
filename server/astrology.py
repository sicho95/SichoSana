"""Horoscope quotidien en français : extrait court Sigastra, crédit visible, cache journalier.

L'astrologie est proposée comme inspiration culturelle et non comme savoir scientifique.
La fonctionnalité reste désactivable par variable SICHOSANA_ASTRO_ENABLED.
Consulter et respecter les conditions de licence avant diffusion publique.
"""
from __future__ import annotations
from datetime import date
import json
import os
import re
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SIGNS = {
    "Bélier": "aries", "Taureau": "taurus", "Gémeaux": "gemini", "Cancer": "cancer",
    "Lion": "leo", "Vierge": "virgo", "Balance": "libra", "Scorpion": "scorpio",
    "Sagittaire": "sagittarius", "Capricorne": "capricorn", "Verseau": "aquarius",
    "Poissons": "pisces",
}
CACHE = {}
LOCK = threading.RLock()
SOURCE_NAME = "Sigastra"
SOURCE_URL = "https://sigastra.com/fr/horoscope-du-jour"


def daily(sign):
    if sign not in SIGNS:
        return {"available": False, "text": "Choisis ton signe dans ton profil.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign}
    if os.environ.get("SICHOSANA_ASTRO_ENABLED", "0") != "1":
        return {"available": False, "text": "L'horoscope du jour n'est pas encore activé.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign}
    key = (date.today().isoformat(), sign)
    with LOCK:
        if key in CACHE:
            return CACHE[key]
    query = urlencode({"lang": "fr", "sign": SIGNS[sign]})
    url = "https://sigastra.com/api/v1/daily?" + query
    public_url = os.environ.get("SICHOSANA_PUBLIC_URL", "https://yoga.sicho.cc.cd").rstrip("/")
    try:
        req = Request(url, headers={"User-Agent": "SichoSana/2.0 (+https://yoga.sicho.cc.cd)",
                                    "Referer": public_url + "/astro-source.html",
                                    "Accept": "application/json"})
        with urlopen(req, timeout=7) as response:
            if response.status != 200:
                raise RuntimeError("HTTP " + str(response.status))
            raw = response.read(80_000)
        payload = json.loads(raw)
        items = payload.get("items") or []
        text = next((x.get("text", "") for x in items if isinstance(x, dict)), "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Extrait vide.")
        text = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", text)
        short = " ".join(sentences[:2])[:420].rstrip()
        if not short:
            raise ValueError("Extrait vide.")
        provider = payload.get("attribution") or {}
        link = provider.get("localizedHref", SOURCE_URL)
        if not isinstance(link, str) or not link.startswith("https://sigastra.com/"):
            link = SOURCE_URL
        result = {"available": True, "text": short, "source": SOURCE_NAME,
                  "sourceUrl": link, "sign": sign, "date": key[0]}
        with LOCK:
            CACHE[key] = result
        return result
    except (OSError, ValueError, RuntimeError, TimeoutError, KeyError) as exc:
        return {"available": False, "text": "La lecture astrologique du jour est temporairement indisponible.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign}
