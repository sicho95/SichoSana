# Procédure de déploiement NAS sans effet de bord

## Principe
Le QNAP possède déjà Cloudflare Tunnel et des services Forgejo / Tailscale en fonctionnement. **Ne pas recréer de tunnel, de DNS générique ou de conteneur partagé** pour SichoSana. Les modifications se limitent au service sichosana et à sa propre route.

## Précontrôle
1. Depuis Forgejo NAS (source officielle), exporter/cloner la branche candidate SichoSana et vérifier le code.
2. Exécuter bash scripts/deploy-nas.sh --check. Ce mode n'effectue aucune mutation.
3. Vérifier docker compose config, disponibilité du port 18765 et état du volume.
4. Vérifier la configuration réseau réelle de cloudflared (hôte ou conteneur, réseau Docker).
5. Assurer un accès de sauvegarde au volume nommé sichosana-data, et ne jamais le supprimer lors d'un upgrade.

## Activation indépendante
1. Configurer .env localement, à l'écart de Git.
2. Lancer bash scripts/deploy-nas.sh --apply. Vérifier /api/v1/health sur l'hôte.
3. Ajouter sur le **tunnel Cloudflare existant** une seule route hostname yoga.sicho.cc.cd vers l'origine SichoSana adaptée à la topologie réseau constatée. En l'état, l'origine publiée par Docker est volontairement en loopback 127.0.0.1:18765 ; depuis un conteneur cloudflared non host-network, localhost pointe sur ce conteneur et pas sur le NAS. Ne jamais supposer son mode réseau.
4. Tester HTTPS et PWA sur un appareil externe, puis accès privé Tailscale suivant les routes existantes ; ne pas confondre les deux.
5. Initialiser les comptes avec les inscriptions temporairement autorisées, puis les refermer.
6. Configurer VAPID uniquement si le push est activé ; les horaires de rappels attendent une décision.

## Critères de recette
- iPhone / iPad / bureau : agencements réellement différents et lisibles.
- Les deux thèmes restent cohérents sur tous les écrans.
- Deux profils, séances sur chacun, export + restauration de **tous** les profils.
- Mode avion après premier chargement : ouvrir l'application et lire les contenus cachés.
- Deux appareils : modifications concurrentes puis fusion des historiques sans suppression de profil.
- Audio Vivienne : identité vérifiée sur manifest, préécoute, validation subjective de la chaleur et du débit, cache hors ligne.
- Notifications uniquement après consentement ; test VAPID requis.
- Anciennes applications NAS, tunnel et routes strictement inchangés.
