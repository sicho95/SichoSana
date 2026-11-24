> **v2.3 — bibliothèque originale publiée, recette en cours.** Les 73 fiches (13 essentielles, 48 Yoga API, 12 compléments) pointent vers 58 PNG canoniques GitHub grâce à 15 alias. Les 183 MP3 et les 60 consignes Soleil/Lune sont inclus. Installation QNAP sans Git et sans ZIP local ; déploiement physique sur NAS et recette sur appareils réels non confirmés.

# SichoSana

PWA française de yoga, méditation et équilibre. Deux thèmes validés : Lin & Sauge et Horizon & Sauge. Interfaces dédiées au téléphone (navigation basse), à l'iPad (navigation horizontale et zones multiples) et à l'ordinateur (barre latérale).

ÉTAT : version 2.3.0 candidate de livraison sur `dev/sichosana-20261105`. Les comptes, SQLite, la configuration locale, Cloudflare et Tailscale restent conservés par le script QNAP.

## Fonctionnalités implémentées

- Accueil, catalogue Hatha/Vinyasa, 6 routines, 13 postures locales éditorialisées + 48 postures Yoga API figées.
- Chronomètre de séance, instructions, pause / reprise, historique.
- 6 méditations et 3 intensités de parole : discrète, équilibrée, enveloppante.
- 183 extraits audio pré-générés V2, dont 60 pour les salutations avec identité strictement conservée de la coach féminine Running ResurGo Fitness (non affichée côté utilisateur). Yoga -22 %, méditation -32 % et pauses supplémentaires ; validation d'écoute à obtenir.
- Inspiration astrologique symbolique locale suivant un signe facultatif, sans affirmation de prévision réelle.
- Comptes utilisateur par pseudo unique et insensible à la casse, inscription en attente de validation par admin, panneau des comptes, email de bienvenue et de réinitialisation, mot de passe modifiable. Bootstrap admin Sicho interactif sur NAS uniquement.
- Profils multiples par compte, IndexedDB, synchronisation automatique invisible, favoris, progression, export/import JSON, service worker PWA hors ligne, pack audio téléchargeable.
- Fonds photographiques ; 58 PNG originaux SichoSana pour 73 références de postures. Aucun ancien visuel tiers n'est choisi lorsque la bibliothèque originale complète est disponible.
- 400 réflexions quotidiennes candidates sans répétition exacte sur les dix derniers jours ; source française Sigastra avec attribution publique, à activer dans .env après vérification du site partenaire.
- Serveur Python 3.12 / SQLite, authentification multi-appareils via code/mot de passe et jeton par appareil, hachage PBKDF2, synchronisation avec révision, fusion des historiques.
- Docker Compose QNAP sans arrêt d'autres conteneurs, sauvegardes SQLite, scripts de précontrôle et CI.

## Démarrer en local

    python -m server.app
    python -m unittest discover -s tests -v

L'application est disponible sur http://127.0.0.1:8080. D'abord lire docs/DEPLOIEMENT_QNAP.md avant un lancement sur le NAS. Le programme n'appelle ni Yoga API ni la synthèse vocale pendant les séances.

## Fichiers de référence

- docs/DECISIONS_2026-11-05.md : spécifications et choix.
- docs/DEPLOIEMENT_QNAP.md : réseau, Cloudflare, Forgejo, Tailscale, recette.
- docs/LICENCES_ET_SOURCES.md : sources Yoga API, crédits Flaticon et voix.
- scripts/generate-voice-pack.py : voix Vivienne.
- scripts/import-yoga-api.py : import ponctuel et snapshot autonome.
- tests/test_server.py et tests/ui.spec.cjs : tests API et navigateur.

## Reste à réaliser ou valider

- Écrans sur vrais iPhone/iPad/ordinateur en comparaison aux maquettes graphiques, avec illustrations détaillées de postures encore à intégrer.
- Écoute et approbation de la diction Vivienne, un peu plus chaleureuse et un peu plus lente.
- Mise à jour NAS-DAMIEN V2.1 par SSH, confirmation audio Safari et SMTP Gmail local à configurer. Ne pas déployer le mode test.
- Web push réel : horaires de rappel, consentement et VAPID non définis, donc non activé.
- Traduction et contrôle des consignes des 48 postures API supplémentaires.

Une CI verte n'est pas une preuve de déploiement NAS ni de qualité sonore approuvée.

## Livraison QNAP v2.3 — sans Git

Le script `scripts/upgrade-v2.3-no-git-qnap.sh` accepte `--check` (aucun changement de production) et `--apply` (précontrôles puis installation). Utiliser `SICHOSANA_REF` avec le SHA complet de la version livrée, sans télécharger de ZIP séparé. Le script vérifie les 58 PNG, les 183 MP3, les catalogues, les tests Python/JS, construit un conteneur isolé, préserve `.env`, Compose et SQLite, puis ne recrée que SichoSana. En cas d'échec, il restaure les sources et l'image précédente ; la base SQLite n'est pas écrasée. Aucune synchronisation Forgejo à ce stade.
