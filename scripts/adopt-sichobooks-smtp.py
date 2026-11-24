#!/usr/bin/env python3
"""Reprendre sans affichage les paramètres SMTP Gmail du worker SichoBooks.

Entrée : docker inspect sichobooks-worker-1 sur stdin ; pas d'authentifiants
sur la ligne de commande, dans le dépôt GitHub ou dans les journaux.
La configuration est écrite atomiquement dans .env après vérification.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import sys


def select(env, names):
    for name in names:
        raw = env.get(name, "")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def configuration_from_inspect(raw):
    if not isinstance(raw, list) or len(raw) != 1:
        raise ValueError("Un seul conteneur SichoBooks est attendu.")
    name = raw[0].get("Name", "").lstrip("/")
    if name != "sichobooks-worker-1":
        raise ValueError("Conteneur source non reconnu : le worker SichoBooks est requis.")
    env = dict(x.split("=", 1) for x in raw[0].get("Config", {}).get("Env", []) if "=" in x)
    host = select(env, ["SICHOBOOKS_SMTP_HOST", "SMTP_HOST"])
    port = select(env, ["SICHOBOOKS_SMTP_PORT", "SMTP_PORT"]) or "465"
    username = select(env, ["SICHOBOOKS_SMTP_USER", "SMTP_USER", "SMTP_USERNAME"])
    password = select(env, ["SICHOBOOKS_SMTP_PASSWORD", "SMTP_PASSWORD", "SMTP_PASS"])
    sender = select(env, ["SICHOBOOKS_SMTP_FROM", "SMTP_FROM"])

    if host not in ("smtp.gmail.com", "smtp.googlemail.com"):
        raise ValueError("Le serveur SichoBooks n'est pas identifié comme Gmail ; aucun changement.")
    if port not in ("465", "587"):
        raise ValueError("Port SMTP Gmail inattendu ; aucun changement.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", username):
        raise ValueError("Compte Gmail source manquant ou invalide ; aucun changement.")
    if not password or len(password) > 256:
        raise ValueError("Mot de passe SMTP SichoBooks manquant ; aucun changement.")
    # Pour éviter une adresse From non autorisée, utiliser la valeur
    # configurée sur SichoBooks uniquement si c'est un simple email.
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", sender):
        sender = username
    values = {
        "SICHOSANA_SMTP_HOST": host,
        "SICHOSANA_SMTP_PORT": port,
        "SICHOSANA_SMTP_SECURITY": "ssl" if port == "465" else "starttls",
        "SICHOSANA_SMTP_USER": username,
        "SICHOSANA_SMTP_PASSWORD": password,
        "SICHOSANA_SMTP_FROM": sender,
    }
    if any(("\n" in v or "\r" in v or "\x00" in v or "#" in v or "$" in v) for v in values.values()):
        raise ValueError("Variable incompatible avec le format .env ; aucun changement.")
    return values


def main():
    try:
        config = configuration_from_inspect(json.load(sys.stdin))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # Les erreurs de validation ne contiennent jamais les valeurs sensibles.
        raise SystemExit(str(exc)) from None

    path = Path(".env")
    if not path.is_file():
        raise SystemExit(".env introuvable : aucune donnée modifiée.")
    previous = path.read_text(encoding="utf-8")
    retained = [line for line in previous.splitlines()
                if not line.startswith("SICHOSANA_SMTP_")]
    backup = path.with_name(".env.bak." + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.write_text(previous, encoding="utf-8")
    backup.chmod(0o600)
    updated = "\n".join(retained + [""] + [k+"="+v for k,v in config.items()]) + "\n"
    tmp = path.with_name(".env.smtp.tmp")
    try:
        tmp.write_text(updated, encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    print("SMTP_SICHOBOOKS_REPRIS_OK : hôte, port, utilisateur, secret et expéditeur.")
    print("Le secret reste uniquement dans .env local, mode 0600.")


if __name__ == "__main__":
    main()
