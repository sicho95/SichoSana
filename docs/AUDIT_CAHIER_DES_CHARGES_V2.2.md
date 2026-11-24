# SichoSana — audit de conformité du cahier des charges initial

**Date : 5 novembre 2026 — candidat V2.2**  
**Statut : corrections versionnées, pas encore validées sur NAS/iPhone.**

## Règles initiales retrouvées

1. Charte Lin & Sauge et Horizon & Sauge : utiliser une interface native sur iPhone, une vraie maquette iPad et un vrai agencement desktop, sans zoom ni reprise de logos génériques. Appliquer cette règle à chaque évolution.
2. Bibliothèque Hatha/Vinyasa locale autonome issue de **Yoga API** (import initial, pas d'appel pendant les séances), avec noms/sanskrit, niveau, description, respiration, alignement, variantes et précautions.
3. Images : PNG officiels référencés dans Yoga API. Images rouges CC0, roses **monkik** et vertes **dDara** depuis Flaticon ; liens de crédit regroupés discrètement dans Profil/Administration.
4. Progression pédagogique : découvrir une posture par étapes, préparation et mouvements d'initiation, version simplifiée, puis position finale lorsque le pratiquant est prêt.
5. Séances quotidiennes choisies selon le niveau, les préférences et les séances déjà effectuées. Programme pluri-jours, sans imposer une posture difficile aux débutants.
6. Voix préenregistrée féminine **fr-FR-VivienneMultilingualNeural** à identité identique à celle du coach Running ResurGo, adaptée yoga (-22 %) et méditation (-32 %) ; pas de TTS navigateur de substitution.
7. Synchronisation automatique par compte de tous les profils, sauvegarde SQLite persistante et fonctionnement local/offline.
8. Emails d'inscription/validation/récupération configurés côté NAS, en reprenant le fonctionnement SMTP déjà éprouvé sur SichoBooks sans exposer de secrets.

## Audit technique

| Élément | Implémenté ou corrigé | Reste à contrôler |
| --- | --- | --- |
| Bibliothèque autonome | 13 postures éditoriales + snapshot de 48 fiches Yoga API, aucun besoin d'appeler l'API au cours d'une séance | Traduction et relecture des 48 descriptions d'origine anglaises |
| Visuels API | Script de récupération local des PNG officiels sur le NAS ; correspondances exactes pour 9 des 13 fiches éditoriales | 4 postures non couvertes : montagne, chien tête en bas classique, cobra doux, torsion allongée. Ne jamais substituer des photos incorrectes |
| Attribution | Liens directs Yoga API, CC0, Flaticon roses monkik et verts dDara dans Profil ; aucune image Flaticon copiée vers GitHub | Vérification juridique détaillée des droits pour chaque style/image, notamment si usage commercial |
| Initiation | 13 guidances comprenant préparation, version douce, respiration, alignement, précautions | Contrôle pédagogique et sécurité sur vrais utilisateurs |
| Séances progressives | 3 modes : Découvrir pas à pas, Version douce, Pratique complète ; deux nouveaux types de clips par posture | Équilibre des durées et transitions à vérifier en recette |
| Séance du jour | Sélection stable par journée selon heure, durée souhaitée, intention, mode de pratique, historique et favoris ; évite une routine récente | Ce n'est pas un programme médical ni un coach expert adaptatif |
| Voix | Identité Vivienne conservée, pack de 111 MP3 pré-générés, test d'intégrité et support HTTP Range 206 pour Safari | Essai réel sur Safari iPhone/Mode PWA ; qualité de diction |
| Email | Deux scripts : reprise SMTP Gmail depuis variables Docker SichoBooks lorsque identifiable, sinon réglage Gmail interactif protégé | Config réelle SichoBooks non consultable depuis GitHub ; aucune reprise effective sans SSH NAS |
| Infrastructure | Réseau Docker bridge standard, NAS IP 192.168.1.69:18887, tunnel existant | Vérifier après mise à jour HTTPS/public et accès Tailscale privé |

## Principes de prudence

Les illustrations des sources extérieures ne sont jamais redessinées à partir de Flaticon par IA. Les visuels de Yoga API ne deviennent pas libres du seul fait que leur API est sous licence MIT ; crédit et conditions du titulaire sont conservés. Les fichiers téléchargés sont uniquement placés dans le cache local NAS, ignoré par Git.

Les photographies Wikimedia intégrées antérieurement sont **désormais retirées de la sélection de la bibliothèque de postures**. Leur présence historique dans le dépôt n'est pas une autorisation de réutilisation.

## Mise à jour du NAS

Une sauvegarde SQLite est créée avant reconstruction, avec aucune commande d'arrêt des autres applications. Depuis le clone NAS déjà installé :

```sh
cd /share/CE_CACHEDEV1_DATA/SichoSana/app
git fetch origin dev/sichosana-20261105
git merge --ff-only FETCH_HEAD
sh scripts/upgrade-v2.2-qnap.sh
```

Le script récupère les images Yoga API directement sur le NAS avant `docker compose up`. Contrôler les 48 téléchargements dans les sorties du script, puis `https://yoga.sicho.cc.cd/api/health` doit indiquer `2.2.0`.

Le SMTP Gmail de SichoBooks peut être repris **localement** si SichoBooks expose ses paramètres dans les variables d'environnement de son conteneur :

```sh
sh scripts/configure-smtp-from-sichobooks-qnap.sh
```

Si la configuration n'est pas disponible, ce script n'effectue **aucune modification**. Utiliser alors `sh scripts/configure-smtp-gmail-qnap.sh` et un mot de passe d'application Google, saisi exclusivement sur le NAS.

**Recette nécessaire :** étudier les 3 modes, écouter préparation et variation douce, essayer un parcours multi-jours, tester la sélection quotidienne sur deux profils distincts, vérifier les images présentes et leurs crédits, et valider mails d'inscription/approbation/récupération.
