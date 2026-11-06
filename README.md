# SichoSana

PWA française de yoga, méditation et équilibre. Deux thèmes validés : Lin & Sauge et Horizon & Sauge. Interfaces dédiées au téléphone (navigation basse), à l'iPad (navigation horizontale et zones multiples) et à l'ordinateur (barre latérale).

ÉTAT : version de recette V2.1 sur la branche dev/sichosana-20261105 ; l'instance NAS existante n'est mise à jour que lorsque le script SSH local est exécuté. Voir docs/RECETTE_V2.1.md pour la migration non destructive, les contrôles et les limites graphiques.

## Fonctionnalités implémentées

- Accueil, catalogue Hatha/Vinyasa, 6 routines, 13 postures locales éditorialisées + 48 postures Yoga API figées.
- Chronomètre de séance, instructions, pause / reprise, historique.
- 6 méditations et 3 intensités de parole : discrète, équilibrée, enveloppante.
- 85 extraits audio pré-générés V2 avec identité strictement conservée de la coach féminine Running ResurGo Fitness (non affichée côté utilisateur). Yoga -22 %, méditation -32 % et pauses supplémentaires ; validation d'écoute à obtenir.
- Inspiration astrologique symbolique locale suivant un signe facultatif, sans affirmation de prévision réelle.
- Comptes utilisateur par pseudo unique et insensible à la casse, inscription en attente de validation par admin, panneau des comptes, email de bienvenue et de réinitialisation, mot de passe modifiable. Bootstrap admin Sicho interactif sur NAS uniquement.
- Profils multiples par compte, IndexedDB, synchronisation automatique invisible, favoris, progression, export/import JSON, service worker PWA hors ligne, pack audio téléchargeable.
- Photographies PNG locales (fonds réels et sept postures détaillées), bibliothèque à onglet et crédit d'images ; six postures locales supplémentaires attendent une illustration adaptée.
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
