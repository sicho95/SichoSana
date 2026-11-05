# SichoSana

PWA française de yoga, méditation et équilibre. Deux thèmes validés : Lin & Sauge et Horizon & Sauge. Interfaces dédiées au téléphone (navigation basse), à l'iPad (navigation horizontale et zones multiples) et à l'ordinateur (barre latérale).

ÉTAT : branche de développement dev/sichosana-20261105 du GitHub privé sicho95/SichoSana. Pas encore transféré au Forgejo canonique sur NAS ni déployé sur yoga.sicho.cc.cd.

## Fonctionnalités implémentées

- Accueil, catalogue Hatha/Vinyasa, 6 routines, 13 postures locales éditorialisées + 48 postures Yoga API figées.
- Chronomètre de séance, instructions, pause / reprise, historique.
- 6 méditations et 3 intensités de parole : discrète, équilibrée, enveloppante.
- 85 extraits audio pré-générés avec l'identité strictement conservée de la coach féminine Running ResurGo Fitness : fr-FR-VivienneMultilingualNeural. Débit -12 %, hauteur -1 Hz candidats ; validation d'écoute à obtenir.
- Inspiration astrologique symbolique locale suivant un signe facultatif, sans affirmation de prévision réelle.
- Profils multiples, IndexedDB, favoris, progression, export/import JSON complet de tous les profils, service worker PWA hors ligne, pack audio téléchargeable.
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
- Configuration effective Forgejo canonique, Cloudflare Tunnel nas-sicho, URL yoga.sicho.cc.cd et accès privé Tailscale, après précontrôle NAS.
- Web push réel : horaires de rappel, consentement et VAPID non définis, donc non activé.
- Traduction et contrôle des consignes des 48 postures API supplémentaires.

Une CI verte n'est pas une preuve de déploiement NAS ni de qualité sonore approuvée.
