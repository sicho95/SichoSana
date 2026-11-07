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
