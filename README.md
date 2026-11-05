# SichoSana

PWA bien-être française : **yoga Hatha / Vinyasa, méditation guidée, astrologie d'inspiration**, progression et profils multiples.

**État : branche de développement, non publiée, non déployée sur NAS.**
**Source de référence de travail prévue : Forgejo sur NAS ; GitHub privé : miroir.**

## Application

- Présentation adaptée séparément pour iPhone (navigation basse), iPad (navigation horizontale et tableaux) et ordinateur (navigation latérale).
- Deux thèmes : **Lin & Sauge**, **Horizon & Sauge**. Les corrections et nouvelles fonctions doivent utiliser les tokens de static/styles.css.
- Six parcours de yoga Hatha/Vinyasa ; bibliothèque initiale de 13 postures décrites (illustrations à importer après revue de licence).
- Six méditations avec trois niveaux de présence vocale : discrète, équilibrée, enveloppante.
- Voix de référence obligatoire : **Vivienne Multilingual Neural française**, exactement celle de la coach Running féminine de ResurGo_Fitness. Candidat plus lent et doux, à valider à l'écoute.
- Séances guidées, historique de pratique, profils multiples, thème et signe astrologique par espace.
- Persistance locale IndexedDB, export/import JSON de tous les profils et historiques, service worker hors connexion.
- Synchronisation NAS par compte : authentification, révisions optimistes, fusion des profils et séances, SQLite en volume Docker.
- Web Push opt-in, nécessite les clés VAPID. Les horaires automatiques ne sont pas choisis et **aucune notification récurrente n'est programmée**.

## Démarrer le frontend local

Python ou tout serveur statique qui sert le dossier static à la racine :

    cd static
    python3 -m http.server 8765

Sur localhost, PWA et stockage sont utilisables. Les points API de synchronisation sont disponibles uniquement depuis le serveur FastAPI.

## Démarrer avec API NAS

    cp env.example .env
    docker compose config
    docker compose up -d --build sichosana

L'application écoute sur **127.0.0.1:18765** sur l'hôte NAS. Base SQLite en volume nommé **sichosana-data**. Rien ne modifie Cloudflare, Tailscale ou Forgejo.

Pour une mise à jour prudente :

    bash scripts/deploy-nas.sh --check
    bash scripts/deploy-nas.sh --apply

Les inscriptions sont fermées par défaut ; mettre temporairement SICHOSANA_REGISTRATION_ENABLED=1 dans le fichier .env pour créer les comptes, puis refermer. Authentification par identifiant et mot de passe de 12 caractères minimum. Prévoir filtrage/rate-limit côté tunnel Cloudflare avant exposition publique.

**Cloudflare :** ajouter uniquement une nouvelle route publique **yoga.sicho.cc.cd** au tunnel NAS existant (ne pas créer un deuxième tunnel), selon le réseau réel du conteneur cloudflared. La publication du point local sur le réseau cloudflared doit être vérifiée sur le NAS, elle n'est **pas automatisée ici**. Prévoir séparément l'accès privé Tailscale déjà en place.

## Voix Vivienne

    python -m pip install "edge-tts>=7,<9"
    python scripts/generate-voice-pack.py --jobs 3

La génération a besoin du réseau uniquement à la préparation du pack. Aucun appel de synthèse en cours de séance. Le workflow GitHub génère également un artefact de pré-écoute candidat. Sans pistes générées : le lecteur affiche une absence audio et laisse les séances silencieuses, sans substitution par une autre voix.

## Qualité

    python -m pip install -r server/requirements.txt pytest httpx
    python -m pytest -q server/tests
    node --check static/app.js

## Licence et postures

Source technique d'import envisagée : Yoga API, https://github.com/alexcumplido/yoga-api. L'API distingue illustrations CC0 et illustrations Flaticon avec crédits obligatoires. Ne pas importer ni sous-licencier aveuglément les images, vérifier les droits pour chaque style avant les mettre hors ligne. Les consignes de pratique proposées ici sont indicatives, pas médicales.

Référence des exigences : docs/DECISIONS_2026-11-05.md. Voir également docs/DEPLOIEMENT_NAS.md.
