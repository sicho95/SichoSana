#!/usr/bin/env python3
"""Réutiliser uniquement une configuration SMTP Gmail de SichoBooks trouvée
dans les variables d'environnement de son conteneur Docker.

L'entrée JSON provient de 'docker inspect' via stdin. Aucun secret n'est affiché.
En cas de configuration absente/ambiguë, ne modifie rien et utiliser le
script de saisie manuelle Gmail existant.
"""
import json
import os
from pathlib import Path
import re
import sys

def pick(values, keys):
    for key in keys:
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

def main():
    raw = json.load(sys.stdin)
    if not isinstance(raw,list) or len(raw)!=1:
        raise SystemExit("Conteneur source ambigu.")
    env = {}
    for line in raw[0].get("Config",{}).get("Env",[]):
        if "=" in line:
            key,value=line.split("=",1)
            env[key] = value
    host=pick(env,["SMTP_HOST","SMTP_SERVER","MAIL_HOST","EMAIL_HOST","SICHOBOOKS_SMTP_HOST"])
    port=pick(env,["SMTP_PORT","MAIL_PORT","EMAIL_PORT"]) or "465"
    sender=pick(env,["SMTP_FROM","SMTP_SENDER","MAIL_FROM","MAIL_FROM_ADDRESS","EMAIL_FROM"])
    username=pick(env,["SMTP_USER","SMTP_USERNAME","MAIL_USERNAME","EMAIL_HOST_USER","MAIL_USER"])
    password=pick(env,["SMTP_PASSWORD","SMTP_PASS","MAIL_PASSWORD","MAIL_PASS","EMAIL_HOST_PASSWORD","GMAIL_APP_PASSWORD"])
    # Reprend le SMTP de SichoBooks uniquement si ce sont exactement les
    # paramètres Gmail attendus. Ne jamais recopier d'autres secrets.
    if (host not in {"smtp.gmail.com","smtp.googlemail.com"} or port not in {"465","587"}
            or not username or not password or not re.fullmatch(r"[a-zA-Z0-9]{16}",password.replace(" ",""))):
        raise SystemExit("SMTP Gmail non identifiable dans SichoBooks : aucune donnée modifiée. Utiliser sh scripts/configure-smtp-gmail-qnap.sh.")
    if username.casefold()!="sicho95@gmail.com":
        raise SystemExit("L'expéditeur SichoBooks n'est pas sicho95@gmail.com : aucune donnée modifiée. Utiliser le script Gmail interactif.")
    password=password.replace(" ","")
    path=Path(".env")
    if not path.exists():
        example=Path(".env.example")
        if not example.exists():
            raise SystemExit("Fichier .env.example absent.")
        path.write_bytes(example.read_bytes())
    previous=path.read_text(encoding="utf-8")
    kept=[line for line in previous.splitlines() if not line.startswith("SICHOSANA_SMTP_")]
    config={
        "SICHOSANA_SMTP_HOST":"smtp.gmail.com",
        "SICHOSANA_SMTP_PORT":port,
        "SICHOSANA_SMTP_SECURITY":"ssl" if port=="465" else "starttls",
        "SICHOSANA_SMTP_USER":username,
        "SICHOSANA_SMTP_PASSWORD":password,
        "SICHOSANA_SMTP_FROM":username,
    }
    for v in config.values():
        if "\n" in v or "\r" in v or "#" in v or "$" in v:
            raise SystemExit("Paramètre non compatible avec .env : aucune donnée modifiée.")
    from datetime import datetime, timezone
    backup=path.with_name(".env.bak."+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.write_text(previous,encoding="utf-8")
    os.chmod(backup,0o600)
    new="\n".join(kept+[""]+[k+"="+v for k,v in config.items()])+"\n"
    tmp=path.with_name(".env.smtp.tmp")
    tmp.write_text(new,encoding="utf-8")
    os.chmod(tmp,0o600)
    tmp.replace(path)
    print("SMTP_GMAIL_REPRIS_DE_SICHOBOOKS : paramètres copiés localement, aucun secret affiché.")

if __name__=="__main__":
    main()
