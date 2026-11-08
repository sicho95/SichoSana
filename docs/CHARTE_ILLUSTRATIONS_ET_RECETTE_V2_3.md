## Mise à jour du 8 novembre 2026 (après cet audit historique)

- **73 fichiers originaux candidats / 73 identifiants actifs** dans le bundle `SichoSana_V2.3_73_illustrations_originales.zip` : 48 Yoga API, 13 essentielles et 12 transitions Soleil/Lune.
- Les quatre derniers mouvements ont été composés/retouchés à partir des visuels cohérents de la professeure, sans changer sa tenue ; vérifier particulièrement la netteté de ces petites sources et l'orientation de la flexion latérale.
- Les 60 nouveaux MP3 des salutations sont présents dans le dépôt (183 MP3 au total). Contrôle Safari physique et déploiement NAS encore nécessaires.
- Les mentions « 38 sur 48 » et « dix manquantes » ci-dessous sont conservées comme **état historique au 7 novembre**, plus comme état courant.

# SichoSana — V2.3, charte illustrations et audit de bibliothèque

## Identité immuable de la professeure (visuels originaux)
- Une seule jeune femme adulte fictive, peau claire, visage doux et calme, cheveux bruns attachés en chignon bas.
- Débardeur ajusté **sauge** (teinte uniforme), leggings **anthracite** foncé, pieds nus, aucune tenue rouge, noire sur le haut ni changement de modèle.
- Silhouette entière, membres présents, épaules/bassin cohérents, regard et tête raccordés à l'orientation du sternum. **Aucune rotation cervicale impossible**.
- Rendu semi-réaliste/illustration soignée, éclairage studio doux, fond transparent PNG. Format lisible dans une vignette mobile et adaptable tablette/ordinateur ; sujet complet dans le cadre, avec marge périphérique.
- Aucune transformation anatomique incertaine admise sous prétexte de cohérence graphique. Croiser avec une référence photographique de la pose réelle, puis valider l'illustration avant publication.

## Audit du 7 novembre 2026
Le catalogue figé de `static/data/yoga-api-library.json` comporte exactement **48 postures distinctes**, en complément des 13 fiches éditoriales.

**38 illustrations individuelles candidates** ont pu être appariées à ces 48 identifiants sur les fichiers générés. Elles restent à contrôler visuellement, leur existence ne constitue pas une validation anatomique.

**10 images absentes, incorrectes ou avec correspondance insuffisante**, interdites de substitution :
- `yoga-api-2` : Half Boat (Ardha Nāvāsana)
- `yoga-api-20` : Forward Bend with Shoulder Opener (Uttānāsana avec ouverture épaules)
- `yoga-api-22` : Handstand (Adho Mukha Vṛkṣāsana)
- `yoga-api-27` : Plow (Halāsana)
- `yoga-api-28` : Pyramid (Pārśvottānāsana)
- `yoga-api-33` : Shoulder Stand (Sālamba Sarvāṅgāsana)
- `yoga-api-36` : Splits (Hanumānāsana)
- `yoga-api-39` : Crescent Moon (Ashta Chandrāsana)
- `yoga-api-43` : Upward-Facing Dog (Ūrdhva Mukha Śvānāsana) — versions de planche inversée refusées : torse et visage incohérents
- `yoga-api-48` : Wild Thing (Camatkārāsana)

**Important :** certains intitulés/sanskrit du snapshot Yoga API sont contradictoires (par ex. Dolphin / Pincha, Downward Dog / Parivrtta). Relire avant d'enseigner.

## Insertion dans la PWA
- Réserver des ressources nommées selon l'identifiant de catalogue, comme `yoga-api-19.png`.
- Ne pas activer de préférence d'affichage automatique avant transfert réel des PNG sur NAS et audit humain. Maintenir les images Yoga API référencées et leurs crédits tant qu'elles sont utilisées.
- Dès que l'app n'affiche plus de contenu Flaticon ou tiers, supprimer les crédits correspondants **du parcours visible**, mais conserver les notices juridiques de provenance pour les contenus encore embarqués/redistribués.

## V2.3 — évolutions techniques distinctes des images
- Audio : corrigé au niveau du service worker, qui tentait de mettre en cache des réponses HTTP 206. Nouveau code capable de répondre aux requêtes partielles depuis le MP3 entier en cache, ou d'utiliser le réseau sans enregistrer les fragments. Lecture `new Audio(url)` rapprochée du fonctionnement ResurGo Running.
- Interface : sélecteurs glissants iOS Yoga, intensité de méditation et périodes astrologiques, action « Mes séances / Bibliothèque » réparée, dominantes lin/beige et cartes mobiles resserrées.
- Tests automatisés : scénario Range audio 206 + cache, et comportement des sélecteurs au glissement et au clic.
- Cette branche est **candidate seulement** : aucune affirmation de déploiement sur le QNAP ni de confirmation sonore sur véritable iPhone avant recette.


## Audit renforcé — 8 novembre 2026

Contrôles sur les **fichiers textuels réellement présents dans GitHub** :
- 13 fiches essentielles, 48 fiches Yoga API et 12 mouvements additionnels : 73 identifiants uniques, cohérents avec les 73 clés du manifeste.
- Soleil A : 12 étapes, 8 prérequis complets / 7 prérequis doux. L'étape 7 utilise chien tête en haut complet et cobra doux ; l'étape 6 utilise Chaturanga complet et planche en variation douce.
- Lune : 18 étapes, 8 prérequis. Chaque posture référencée existe dans la bibliothèque.
- Voix : manifeste fr-FR-VivienneMultilingualNeural, 183 entrées dont 60 consignes Soleil/Lune, références complètes dans le manifeste.
- Test navigateur ajouté : maîtrise d'une posture, transmission entre deux appareils, révocation et séparation par profil.
- Correctif d'affichage : les originaux ne sont désormais sélectionnés que si l'API confirme réellement les 73 fichiers.

**Différence fondamentale :** 73 clés présentes dans GitHub ne signifient PAS 73 PNG vérifiés. Les binaires originaux ne sont pas stockés dans le dépôt ; leur présence sur NAS ou dans l'archive privée doit être contrôlée avant déploiement.

Le nouvel audit `scripts/verify-v23-art-and-salutations.py` contrôle le contenu effectif du ZIP ou des PNG installés, les correspondances exactes, les empreintes SHA-256 du ZIP, les CRC PNG, les dimensions, les duplications et l'exhaustivité des fichiers audio. Toute erreur doit bloquer l'installation. Le résultat ne garantit toujours pas l'alignement anatomique : revue visuelle obligatoire des postures complexes, en priorité chien tête en haut / cobra, Chaturanga, demi-flexion, flexion latérale et étoile.

Ne jamais déployer directement l'ancien script d'upgrade sans précontrôle complet. Utiliser le script autonome de déploiement vérifié sans Git, avec sauvegarde SQLite et rollback sources, fourni séparément dans le dossier de livraison.
