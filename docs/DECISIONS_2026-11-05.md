# SichoSana — décisions de référence

Daté du 5 novembre 2026. Les points non validés restent des questions, jamais des suppositions.

## Identité et usage
- Application **SichoSana** en français : yoga Hatha / Vinyasa, postures, enchaînements, méditation guidée, astrologie du jour, programmes, suivi et progression.
- Thèmes validés : **Lin & Sauge** et **Horizon & Sauge** (mix retenu des explorations graphiques).
- Charte graphique appliquée **à toute correction et évolution**. Vrais écrans adaptatifs iPhone, iPad et ordinateur, pas de simple zoom.
- PWA installable, hors ligne, profils multiples, synchronisation multi-appareils et web push opt-in.
- Import initial externe des postures puis bibliothèque autonome, avec provenance et licences documentées.

## Voix — contrainte explicite
- Utiliser **exactement l'identité de la coach féminine Running de ResurGo_Fitness** : **fr-FR-VivienneMultilingualNeural** (Edge Neural, pack v2).
- Sources vérifiées dans sicho95/ResurGo_Fitness : scripts/generate-edge-voice-pack.py ; static/voice/fr-FR/v2/manifest.json ; app/voice-pack.js.
- Ne jamais changer l'identité en douce ni utiliser une voix masculine ou un TTS de navigateur non maîtrisé pour remplacer Vivienne.
- SichoSana : **un peu plus lente, légèrement plus chaleureuse**. Réglage V2 candidat : débit yoga -22 %, méditation -32 %, hauteur -1Hz, volume +0 %, pauses renforcées. La sensation de chaleur dépend également des textes et des pauses. **Validation auditive encore nécessaire**, ne pas la prétendre acquise.
- Générer des fichiers audio dédiés aux séances de yoga et aux méditations, pré-générés, versionnés et vérifiés par SHA-256 ; lecture hors ligne sans service de synthèse en temps réel.
- Si le pack n'est pas disponible, annoncer explicitement « audio indisponible » : aucune substitution silencieuse.

## Infrastructure
- URL publique cible : https://yoga.sicho.cc.cd.
- Réutiliser le Cloudflare Tunnel NAS existant, ajouter uniquement la route SichoSana ; garder séparé l'accès privé des membres Tailscale/Funnel existant.
- Dépôt canonique de travail **Forgejo sur NAS** ; miroir privé **sicho95/SichoSana sur GitHub**.
- La branche dev/sichosana-20261105 du miroir GitHub est la préparation active. Le déploiement initial a été réalisé sur le NAS le 5 novembre 2026 et l'accès yoga.sicho.cc.cd fonctionne ; la V2.2 n'est pas encore installée sur le NAS. Vérification de la synchronisation avec le Forgejo canonique encore nécessaire.
- Déploiement Docker Compose non destructif, volume SQLite persistant, frontend local-first et sauvegarde/export.

## Questions à Damien (uniquement lorsqu'elles deviennent bloquantes)
- Calendrier exact des notifications Web Push (rappels).
- Source française Sigastra retenue comme candidat, mais son usage dans une PWA privée nécessite validation des conditions de syndication.
- Validation à l'écoute de la légère adaptation de Vivienne.

## V2 — arbitrages explicites validés par Damien

Date : 5 novembre 2026.

- Design : les écrans de la V1 ne ressemblent pas suffisamment aux maquettes. Reprendre le rendu premium et naturel des versions approuvées, fonds photographiques, vrais logos ; éviter les SVG génériques. Préférer PNG haute qualité, si possible détourés. Respect de la charte Lin & Sauge / Horizon & Sauge dans toute évolution.
- Comptes : onboarding obligatoire, pseudo unique identifiant de connexion (comparaison insensible à la casse après Unicode NFKC), email et mot de passe ; pas de prénom, nom, téléphone ou date de naissance imposés.
- Premier compte admin : pseudo **Sicho**, email **sicho95@gmail.com**, mot de passe initial **provisoire saisi sur le NAS** en mode interactif (valeur demandée : 1234). Ne jamais versionner ni afficher cette valeur dans un fichier de configuration ; changement obligatoire dès la première connexion et mot de passe de 10 caractères minimum ensuite.
- Validation de l'inscription par un membre du groupe **admin** dans le panneau d'administration, pas de lien magique d'acceptation par email. Chaque admin actif reçoit un email annonçant la demande ; l'utilisateur reçoit un email d'attente puis d'acceptation et un message de bienvenue délicat signé « L’équipe de SichoSana ».
- Panneau admin : valider, suspendre, réactiver, supprimer définitivement et attribuer ou retirer le rôle admin. Conserver au moins un admin actif et empêcher l'auto-suppression/auto-destitution.
- Changement du mot de passe dans le profil ; « Mot de passe oublié » via email depuis l'écran de connexion avec lien limité dans le temps.
- Synchronisation : complètement automatique après inscription et connexion, pour **tous** les profils de pratique du compte, avec reprise au retour réseau. Aucun contrôle visible pour l'association ou la « synchronisation NAS ». Garder export/import de sauvegarde volontaire.
- Méditation : même identité vocale que la pratique yoga, plus lente que la voix Yoga, et avec davantage de pauses ; aucun nom de moteur ou modèle de voix dans l'interface.
- Yoga : bibliothèque distincte de 13 postures éditoriales et 48 positions de Yoga API. V2.2 restaure la priorité aux PNG officiels Yoga API, avec crédits Flaticon dans Profil, neuf correspondances précises pour les 13 fiches. Quatre postures restent sans correspondance et les 48 descriptions anglaises doivent être revues. Préparation et variante douce ont été introduites pour les 13 postures, à valider en recette.
- Astrologie : source externe réelle **en français**, texte court (1 à 2 phrases) dans l'univers yoga, réflexion et sérénité. Source candidate Sigastra, à vérifier sur le plan de la republication dans une application avec connexion (API désactivée par défaut).
- Phrase du jour : environ **400** phrases originales, sélection quotidienne, aucune répétition exacte dans les dix derniers jours. Corpus candidat à relire.

## État d'exécution / limites
- Une version V2 de SichoSana a été déployée sur le NAS, avec Docker bridge et route Cloudflare existante vers http://192.168.1.69:18887 ; la V2.2 demeure uniquement candidate jusqu'à l'exécution du script local de mise à jour.
- Le compte Sicho **n'a pas encore été créé sur le NAS**, la messagerie SMTP n'est **pas encore configurée** ; les emails réels ne peuvent être affirmés envoyés.
- Les photographies de fond PNG et sept photographies de postures ont été ajoutées ; **l'approbation de la qualité de la maquette V2 reste à obtenir**.
- La source Forgejo sur NAS reste la référence, et non cette note ni la conversation.

## Révision de conformité V2.2

Voir `docs/AUDIT_CAHIER_DES_CHARGES_V2.2.md` : référentiel Yoga API, crédits monkik/dDara/CC0, étapes pédagogiques, séances quotidiennes selon objectif/durée/historique, voix Vivienne 111 clips, SMTP à reprendre localement depuis SichoBooks, et limites restant ouvertes. Ne jamais déclarer la V2.2 déployée ni le SMTP réutilisé avant la confirmation réelle sur NAS.
