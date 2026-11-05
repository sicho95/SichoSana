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
- SichoSana : **un peu plus lente, légèrement plus chaleureuse**. Réglage provisoire candidat : débit -12 %, hauteur -1Hz, volume +0 %. La sensation de chaleur dépend également des textes et des pauses. **Validation auditive encore nécessaire**, ne pas la prétendre acquise.
- Générer des fichiers audio dédiés aux séances de yoga et aux méditations, pré-générés, versionnés et vérifiés par SHA-256 ; lecture hors ligne sans service de synthèse en temps réel.
- Si le pack n'est pas disponible, annoncer explicitement « audio indisponible » : aucune substitution silencieuse.

## Infrastructure
- URL publique cible : https://yoga.sicho.cc.cd.
- Réutiliser le Cloudflare Tunnel NAS existant, ajouter uniquement la route SichoSana ; garder séparé l'accès privé des membres Tailscale/Funnel existant.
- Dépôt canonique de travail **Forgejo sur NAS** ; miroir privé **sicho95/SichoSana sur GitHub**.
- La branche dev/sichosana-20261105 du miroir GitHub est uniquement un espace de préparation : son contenu n'a pas encore été transféré sur le Forgejo canonique ni déployé.
- Déploiement Docker Compose non destructif, volume SQLite persistant, frontend local-first et sauvegarde/export.

## Questions à Damien (uniquement lorsqu'elles deviennent bloquantes)
- Calendrier exact des notifications Web Push (rappels).
- Source et personnalisation détaillée de l'astrologie si une intégration externe est demandée.
- Validation à l'écoute de la légère adaptation de Vivienne.
