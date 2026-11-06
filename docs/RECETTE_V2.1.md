# SichoSana — V2.1, recette multiplateforme et migration QNAP
Date : 5 novembre 2026. Version préparée sur `dev/sichosana-20261105`.

## Changements intégrés
- Lotus harmonisé entre connexion, en-tête et icône PWA ; disparition de l'étoile provisoire et du S.
- Suppression du header fantôme au-dessus de la page de connexion.
- Navigation mobile à exactement cinq onglets, administration accessible depuis Profil, sans deuxième rangée.
- Titres et cartes Administration réorganisés pour éviter colonnes excessivement étroites ; actions invalides sur son propre compte admin masquées.
- Hauteur de la séance du jour réduite, mise en page iPhone/iPad/desktop harmonisée.
- Uniformisation du format et de la colorimétrie de sept photographies de postures CC avec respect des licences. Personnes photographiées toujours différentes : cela ne constitue PAS une série unifiée autour d'un unique modèle. Six postures éditoriales restent sans photo certifiée.
- Voix ResurGo `fr-FR-VivienneMultilingualNeural` V2 conservée, un seul lecteur réutilisé, commande d'écoute directe, service des fichiers MP3 avec HTTP 206 Range pour Safari iOS, tests automatisés. La validation perceptive sur véritable iPhone reste nécessaire.
- Sigastra en français : quotidien, semaine, mois, signe choisi directement ; crédit visible et page publique `/astro-source.html`. Activer avec `SICHOSANA_ASTRO_ENABLED=1`. Vérification externe du site auprès de Sigastra à réaliser si l'API retourne indisponible.
- SMTP Gmail par secret d'application saisi sur le NAS seulement. Peut être remplacé par une autre adresse à tout moment.

## Upgrade du NAS
Depuis le clone déjà présent sur NAS-DAMIEN :

```sh
cd /share/CE_CACHEDEV1_DATA/SichoSana/app
git fetch origin dev/sichosana-20261105
git merge --ff-only FETCH_HEAD
sh scripts/upgrade-v2.1-qnap.sh
```

Le script sauvegarde SQLite avant toute mise à jour Docker, préserve les volumes, écrit `SICHOSANA_BIND=192.168.1.69`, active la source horoscope, utilise le réseau Docker `bridge` de référence, contrôle l'API et la présence des MP3. Il ne modifie pas les tunnels, le DNS, Tailscale ou les autres applications. Le dépôt GitHub doit être accessible par le NAS, par exemple provisoirement public.

SMTP seulement si un mot de passe d'application Google a été généré après activation de la validation en deux étapes :

```sh
sh scripts/configure-smtp-gmail-qnap.sh
```

Choisir `sicho95@gmail.com`, saisir uniquement dans le terminal local le mot de passe d'application Google de 16 caractères (ne jamais le communiquer dans ChatGPT). Le mot de passe usuel Gmail ne convient pas. Ce script peut ensuite être relancé pour changer l'adresse expéditrice.

## Tests manuels impératifs
1. Comparer connexion, Accueil, Yoga, Méditer, Astro, Profil, Administration sur Safari iPhone, Safari iPad et ordinateur, dans les deux thèmes.
2. Lancer une séance, vérifier la lecture vocale spontanée. Si nécessaire, utiliser « Écouter la consigne » ; tester également la deuxième posture et reprise/pause.
3. Tester l'URL publique `https://yoga.sicho.cc.cd/api/health` et la fonction `/api/v1/content/horoscope?sign=Lion&period=daily`.
4. Tester les profils sur deux appareils sans pertes ni mélange des comptes.
5. Après SMTP Gmail, demander une inscription depuis un deuxième compte, recevoir l'email administrateur, approuver puis recevoir le mail d'activation. Tester mot de passe oublié.
6. Pour les illustrations restantes et le casting visuel unique, fournir ou produire des photos de postures homogènes et vérifier leurs droits, sans employer de postures inventées ou anatomiquement incorrectes.

## Hors périmètre de cette version
Ni compte SMTP ni jeton Google ne sont sauvegardés dans Git. Aucun changement distant automatique sur le NAS n'est effectué par GitHub. La recette iOS, la validation des 13 visuels et la vérification fournisseur Sigastra restent à confirmer sur l'instance réelle. Ne pas qualifier cette version de recette définitive sans ces contrôles.
