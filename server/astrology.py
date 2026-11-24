"""Horoscopes Sigastra FR pour SichoSana, en extrait avec attribution publique.
Conditions partenaires : https://sigastra.com/fr/partners/api
Les appels depuis le NAS portent un Referer vers une page publique qui crédite
Sigastra. Le service reste désactivable immédiatement par variable d'environnement.
"""
from __future__ import annotations
from datetime import date
import json
import os
import re
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SIGNS = {
    "Bélier": "aries", "Taureau": "taurus", "Gémeaux": "gemini",
    "Cancer": "cancer", "Lion": "leo", "Vierge": "virgo",
    "Balance": "libra", "Scorpion": "scorpio", "Sagittaire": "sagittarius",
    "Capricorne": "capricorn", "Verseau": "aquarius", "Poissons": "pisces",
}
PERIODS = {"daily", "weekly", "monthly"}
SOURCE_NAME = "Sigastra"
SOURCE_URL = "https://sigastra.com/fr/horoscope-du-jour"
CACHE = {}
LOCK = threading.RLock()


def daily(sign, period="daily"):
    if period not in PERIODS:
        period = "daily"
    if sign not in SIGNS:
        return {"available": False, "text": "Choisis ton signe dans ton profil.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period}
    if os.environ.get("SICHOSANA_ASTRO_ENABLED", "0") != "1":
        return {"available": False, "text": "La source astrologique est temporairement désactivée.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period}
    key = (date.today().isoformat(), sign, period)
    with LOCK:
        if key in CACHE:
            return CACHE[key]
    params = urlencode({"lang": "fr", "sign": SIGNS[sign]})
    url = f"https://sigastra.com/api/v1/{period}?" + params
    public_url = os.environ.get("SICHOSANA_PUBLIC_URL", "https://yoga.sicho.cc.cd").rstrip("/")
    try:
        req = Request(url, headers={
            "User-Agent": "SichoSana/2.1 (+https://yoga.sicho.cc.cd/astro-source.html)",
            "Referer": public_url + "/astro-source.html",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=9) as response:
            if response.status != 200:
                raise ValueError("HTTP " + str(response.status))
            payload = json.loads(response.read(90_000))
        items = payload.get("items") or []
        if not isinstance(items, list):
            raise ValueError("Données inattendues.")
        item = next((i for i in items if isinstance(i, dict)
                     and isinstance(i.get("text"), str) and i["text"].strip()), None)
        if item is None:
            raise ValueError("Horoscope vide.")
        full_text = re.sub(r"\s+", " ", item["text"]).strip()
        short = " ".join(re.split(r"(?<=[.!?])\s+", full_text)[:3]).strip()[:480]
        attribution = payload.get("attribution") or {}
        link = attribution.get("localizedHref", SOURCE_URL)
        if not isinstance(link, str) or not link.startswith("https://sigastra.com/"):
            link = SOURCE_URL
        result = {"available": True, "text": short, "source": SOURCE_NAME,
                  "sourceUrl": link, "sign": sign, "period": period, "date": key[0]}
        with LOCK:
            CACHE[key] = result
        return result
    except (OSError, ValueError, TypeError, KeyError, HTTPError, URLError):
        # Ne jamais inventer d'horoscope. Garder un lien direct à la source.
        return {"available": False, "text": "Lecture indisponible pour le moment. Tu peux consulter directement la source.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period}
