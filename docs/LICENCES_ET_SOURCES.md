# Sources et droits SichoSana

Source des métadonnées complémentaires : https://github.com/alexcumplido/yoga-api ; API et code source MIT, crédit à Alexandre C. Le snapshot Yoga API de 48 postures est figé dans static/data/yoga-api-library.json. Pas d'appel à Yoga API pendant les séances.

Visuels : Yoga API distingue les images rouges CC0, les images roses attribuées à monkik — https://www.flaticon.com/free-icons/easy — et les vertes attribuées à dDara — https://www.flaticon.com/free-icons/yoga. Pour les visuels Flaticon, attribution obligatoire. Ne pas utiliser la génération IA à partir de ces ressources. SichoSana ne redistribue aucune des images Flaticon issues de Yoga API à ce stade. Sept photographies de postures provenant de Wikimedia Commons ont été sélectionnées avec leurs licences et crédits individuels, dans `static/data/pose-media.json`. Elles ont été converties en PNG (modification technique de format) et leurs licences originales sont conservées.

Identité voix : fr-FR-VivienneMultilingualNeural, identique à la coach féminine Running de ResurGo Fitness (pack v2). Pré-génération des 85 clips V1 (-12 %) ; pack V2 candidat yoga -22 % et méditation -32 %, hauteur -1 Hz, volume neutre, avec pauses de lecture. La voix ne doit pas être nommée dans l'interface. Appropriation à valider à l'oreille.

Thèmes autorisés en V1 : Lin & Sauge, Horizon & Sauge. Les tokens CSS et trois mises en page (mobile / tablette / ordinateur) sont un invariant de design.


## Photographies PNG locales

- `static/media/yoga-hero.png` : photographie yoga, source Unsplash, https://images.unsplash.com/photo-1544367567-0f2fcb009e0b, rééchantillonnée pour l'interface. Crédit à documenter avec la fiche Unsplash originale avant mise en production (photographe à confirmer).
- `static/media/meditation.png` : https://images.unsplash.com/photo-1506126613408-eca07ce68773 ; licence Unsplash.
- `static/media/nature.png` : https://images.unsplash.com/photo-1518495973542-4542c06a5843 ; licence Unsplash.
- Photographies de postures : sélection de https://github.com/jreinjr/yoga-pose-photos, originaux Wikimedia Commons (CC BY 2.0/3.0 ou CC BY-SA 4.0 selon image). Metadata auteur, URL originale, licence et lien : `static/data/pose-media.json`. Crédits visibles dans chaque fiche posture. Les versions PNG ne deviennent pas CC0 ; les licences Creative Commons d'origine demeurent.
- Les 6 autres postures sans photographie restent à illustrer correctement. Ne pas remplacer par des silhouettes SVG génériques.

## Contenu astrologique

- Source candidate : https://sigastra.com/fr/partners/api ; extrait français quotidien de 1 à 2 phrases.
- Exige un lien `Sigastra` visible sur une page accessible publiquement après la période d'essai (et une balise canonical pour texte intégral, non utilisé). `static/astro-source.html` propose cette page publique avec les douze signes.
- Conditions et licence à confirmer par l'éditeur avant activation durable : SichoSana possède une interface de lecture protégée par compte, ce qui n'autorise pas à présumer l'usage commercial/mobile gratuit. L'API reste désactivée par défaut (`SICHOSANA_ASTRO_ENABLED=0`).
- La lecture astrologique reste présentée comme culture et réflexion, jamais comme certitude scientifique.

## Réflexions quotidiennes

`static/data/reflections.json` contient 400 formulations originales candidates, séquencées afin de ne pas répéter une entrée dans les dix derniers jours. Elles demandent encore validation éditoriale avant sortie finale.

## Correction de provenance V2.2

Les photographies Wikimedia précédentes sont conservées comme historique de développement mais **ne sont plus choisies par la bibliothèque SichoSana**. Les postures affichent désormais les images PNG officielles référencées dans le snapshot Yoga API, téléchargées par le NAS au déploiement dans `static/media/yoga-api/`. Les ressources Flaticon ne sont pas committées dans le dépôt GitHub. Les crédits officiels (monkik, dDara, CC0 et Yoga API) se trouvent dans la rubrique **Profil → Sources et crédits des illustrations**. Les références locales correspondant à neuf des treize postures sont identifiées dans `static/data/pose-guidance.json`; quatre restent sans correspondance exacte, à ne pas présenter avec une pose erronée. Les 48 postures importées restent des fiches documentaires non intégrées à des séances sans révision des consignes françaises.

L'application ne reproduit pas ni ne modifie par IA les illustrations Flaticon, conformément à leurs conditions. Vérifier les droits de republication et les éventuelles contraintes supplémentaires de chaque fournisseur avant diffusion commerciale.
