# SichoSana — déploiement QNAP non destructif

Référence 5 novembre 2026. DOCUMENT DE PRÉPARATION : aucun déploiement NAS, DNS ou tunnel n'est déclaré accompli.

## Infrastructure déjà décidée

- Source canonique : Forgejo sur NAS-DAMIEN. Le privé GitHub sicho95/SichoSana est miroir de préparation.
- Route publique cible : https://yoga.sicho.cc.cd.
- Tunnel Cloudflare existant : nas-sicho / conteneur cloudflared-nas-sicho. NE PAS créer un autre tunnel.
- Tailscale déjà présent, avec notamment https://nas-damien.tailfb6907.ts.net et la route /git existante : préserver sa configuration.
- Projet isolé Docker Compose : sichosana ; conteneur sichosana-app ; volume persistant runtime/ ; port candidat 18887.
- Aucune commande de suppression globale de conteneurs ou de réinitialisation Tailscale, Cloudflare, DNS ou volumes.

## Ordre de déploiement

1. Relever l'URL effective du dépôt Forgejo SichoSana (Question à Damien ou audit NAS) avant de transférer la branche GitHub dev/sichosana-20261105 au dépôt canonique.
2. Sur NAS, dans une copie validée de la branche de développement, faire un précontrôle non destructif :

    sh scripts/deploy-qnap.sh --check
    docker ps --format '{{.Names}} {{.Ports}}'
    tailscale serve status --json
    tailscale funnel status

3. Confirmer port 18887 disponible, ressources mémoire, droits d'écriture du volume pour UID 10001, réseau cloudflared. Si un port est utilisé, choisir un autre port non utilisé via SICHOSANA_PORT, sans jamais modifier l'application en place.
4. Après validation explicite de la recette, démarrer exclusivement SichoSana :

    sh scripts/deploy-qnap.sh --apply
    curl --fail http://127.0.0.1:18887/api/health

Le script utilise docker compose -p sichosana up -d --build --no-deps. Il ne redémarre ni n'arrête les autres conteneurs et ne touche à aucune route. SQLite : runtime/sichosana.sqlite3. Sauvegarde cohérente : python server/backup.py --source runtime/sichosana.sqlite3 --dest /chemin/backup/sichosana.sqlite3.

## Cloudflare public

Dans la configuration existante du tunnel nas-sicho, ajouter uniquement un public hostname yoga.sicho.cc.cd relié à l'upstream SichoSana réellement joignable. Ne pas supposer que le 127.0.0.1 du conteneur cloudflared est celui du NAS. Si cloudflared est isolé, vérifier son réseau et l'adresse de l'hôte ; adapter le bind uniquement après revue de sécurité. Tester HTTPS, /, /api/health, /manifest.webmanifest, /sw.js et les assets vocaux.

## Tailscale Serve et Funnel

L'application utilise des chemins absolus à la racine (/app.js, /data, /api, /voice). Ne pas publier sous /yoga sans configuration de réécriture vérifiée. Pour des appareils membres du tailnet, préférer une nouvelle route Serve HTTPS sur un port libre, sans modifier la route /git. Exemple uniquement si port 8443 disponible et après vérification de l'existant :

    tailscale serve --https=8443 --bg http://127.0.0.1:18887

Serve = privé tailnet ; Funnel = exposition publique. Ne pas confondre les deux ni ouvrir accidentellement l'accès privé au public. Cloudflare fournit déjà l'adresse publique souhaitée. Documentation de référence : https://tailscale.com/docs/reference/tailscale-cli/serve et https://tailscale.com/docs/reference/tailscale-cli/funnel.

## Recette avant mise en service

- iPhone : installation, navigation basse, posture, chronomètre, coupure Internet, contenu hors ligne, session en cours.
- iPad : navigation horizontale, colonnes distinctes, paysage et portrait.
- Ordinateur : sidebar, panneau de progression, accessibilité clavier.
- Multiprofils : synchroniser deux appareils et plusieurs profils ; conflit de révision ; export/import complet ; mot de passe invalide ; récupération sans effacement.
- Audio : écouter Vivienne de bout en bout et valider débit/chaleur ; ne jamais remplacer automatiquement sa voix.
- Thèmes : Lin & Sauge et Horizon & Sauge sur tous les écrans et lors d'évolutions.
- Sécurité : vérification séparée DNS, TLS, firewall, protection de l'espace de synchro.
- Notifications : horaires encore non définis, clés VAPID non déployées. Ne rien activer sans décision.

## Limites explicitement ouvertes

Les 48 postures figées de Yoga API ont principalement des descriptions anglaises ; les fichiers graphiques tiers ne sont pas importés avant vérification fine de licence. La charte UI a une implémentation CSS responsive mais doit encore être confrontée aux maquettes sur appareils réels. Le déploiement Forgejo/NAS/Cloudflare/Tailscale et la recette réelle ne sont pas effectués ici.
