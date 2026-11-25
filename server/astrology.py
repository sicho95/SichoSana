"""Horoscopes Sigastra FR pour SichoSana, en extrait avec attribution publique.
Conditions partenaires : https://sigastra.com/fr/partners/api
Les appels depuis le NAS portent un Referer vers une page publique qui crédite
Sigastra. Le service reste désactivable immédiatement par variable d'environnement.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os
import re
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from html.parser import HTMLParser
from html import escape
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


def period_key(period, now=None):
    day = (now or datetime.now(ZoneInfo('Europe/Paris'))).date()
    if period == 'weekly':
        return (day - timedelta(days=day.weekday())).isoformat()
    if period == 'monthly':
        return day.strftime('%Y-%m')
    return day.isoformat()


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "canonical":
            self.href = values.get("href")


def source_canonical(tag):
    parser = CanonicalParser()
    if not isinstance(tag, str):
        raise ValueError("Canonical absent")
    parser.feed(tag)
    parsed = urlsplit(parser.href or "")
    if parsed.scheme != "https" or parsed.netloc != "sigastra.com":
        raise ValueError("Canonical invalide")
    return parser.href


def short_preview(text):
    first = re.split(r"(?<=[.!?])\s+", text.strip())[0]
    return first if len(first) <= 240 else "Ton horoscope du jour est disponible."


def public_reading(sign, period, result):
    canonical = result.get("canonicalUrl")
    head = ('<link rel="canonical" href="'+escape(canonical, quote=True)+'">') if canonical else ""
    label = {"daily":"du jour","weekly":"de la semaine","monthly":"du mois"}[period]
    title = escape(sign + " — Horoscope " + label)
    body = "".join("<p>"+escape(p)+"</p>" for p in result.get("text","").split("\n\n") if p.strip())
    link = escape(result.get("sourceUrl", SOURCE_URL), quote=True)
    return ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+title+' — SichoSana</title>'+head+
            '<link rel="stylesheet" href="/styles.css?v=20261125-r9"></head>'
            '<body><main class="astro-public"><a href="/astro-source.html">Horoscopes publics</a>'
            '<article class="card astrology-card"><h1>'+title+'</h1><div class="astro-quote">'+body+'</div>'
            '<p class="muted">Lecture symbolique, sans prédiction scientifique.</p>'
            '<p>Source : <a href="'+link+'">Sigastra</a></p></article></main></body></html>')


def daily(sign, period="daily"):
    if period not in PERIODS:
        period = "daily"
    if sign not in SIGNS:
        return {"available": False, "text": "Choisis ton signe dans ton profil.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period}
    if os.environ.get("SICHOSANA_ASTRO_ENABLED", "0") != "1":
        return {"available": False, "text": "La source astrologique est temporairement désactivée.",
                "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period, "reason": "disabled"}
    key = (period_key(period), sign, period)
    with LOCK:
        if key in CACHE:
            return CACHE[key]
    params = urlencode({"lang": "fr", "sign": SIGNS[sign], "full": "1"})
    url = f"https://sigastra.com/api/v1/{period}?" + params
    public_url = os.environ.get("SICHOSANA_PUBLIC_URL", "https://yoga.sicho.cc.cd").rstrip("/")
    try:
        headers = {"User-Agent": "SichoSana/2.3.1 (+https://yoga.sicho.cc.cd/astro-source.html)",
                   "Referer": public_url + "/astro-source.html", "Accept": "application/json"}
        partner_key = os.environ.get("SICHOSANA_ASTRO_PARTNER_KEY", "").strip()
        if partner_key:
            headers["x-sigastra-key"] = partner_key
        req = Request(url, headers=headers)
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
        full_text = "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", item["text"].strip()) if p.strip())
        attribution = payload.get("attribution") or {}
        canonical = source_canonical(attribution.get("canonicalTag"))
        link = attribution.get("localizedHref", SOURCE_URL)
        if not isinstance(link, str) or not link.startswith("https://sigastra.com/"):
            link = SOURCE_URL
        result = {"available": True, "text": full_text, "preview": short_preview(full_text), "canonicalUrl": canonical, "full": True, "source": SOURCE_NAME,
                  "sourceUrl": link, "sign": sign, "period": period, "periodKey": key[0], "date": period_key('daily')}
        with LOCK:
            CACHE[key] = result
            if len(CACHE) > 100:
                CACHE.pop(next(iter(CACHE)))
        return result
    except HTTPError as exc:
        reason = "provider_authorization" if exc.code in (401, 403) else "provider_limit" if exc.code == 429 else "provider_http"
    except (OSError, URLError):
        reason = "network"
    except (ValueError, TypeError, KeyError, AttributeError):
        reason = "invalid_response"
    return {"available": False, "text": "L’horoscope est temporairement indisponible. Réessaie dans un instant.",
            "source": SOURCE_NAME, "sourceUrl": SOURCE_URL, "sign": sign, "period": period, "reason": reason}
