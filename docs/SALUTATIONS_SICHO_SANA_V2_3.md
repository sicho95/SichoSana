# SichoSana V2.3 — Salutations guidées vérifiées

## Choix terminologique validé

- **Salutation au soleil A** (Sūrya Namaskār A). Formulation de référence en français, attestée par TERMIUM Plus, Bureau de la traduction du Canada : https://www.btb.termiumplus.gc.ca/tpv2alpha/alpha-eng.html?index=alt&srchtxt=SURYA+NAMASKAR
- **Salutation à la lune** (Chandra Namaskār), adaptée de la séquence classique décrite par Kripalu : https://kripalu.org/living-kripalu/chandra-namaskar-honoring-moon-salute
- Ne pas employer **« Salut au soleil »** comme titre final : moins conforme à la terminologie officielle. « Salutation du soleil » n'est pas le libellé retenu.

## Cobra vs chien tête en haut — distinction obligatoire

- **Ūrdhva Mukha Śvānāsana / chien tête en haut** : bras tendus, poitrine ouverte, dessus des pieds en appui, **cuisses et bassin décollés du sol**, sans torsion impossible de la nuque.
- **Bhujangāsana / cobra** : bassin, pubis et cuisses **au sol**, extension plus modérée du dos, éventuellement coudes fléchis.
- La **Salutation au soleil A Vinyasa/Ashtanga** emploie chien tête en haut. Notre version **douce** permet de choisir cobra après une descente genoux au sol. Dans certaines versions **Hatha classiques**, cobra est la posture de base, et non simplement une adaptation.
- Références : https://ashtanga.tech/study-guide/yoga-techniques/asana/surya-namaskar-vinyasa-yoga/surya-namaskar-asana-sequences/ et https://www.yogacanada.com/yoga-poses-and-asanas/yoga-sun-salutation-a-surya-namaskar-a/
- L'illustration d'enchaînement **« Salut au soleil »** produite en maquette ne suffit pas comme image pédagogique : elle rend très peu visible l'écart cobra/chien tête en haut. Ne pas l'utiliser dans les cours.

## Deux séquences retenues

La source de vérité exécutable est `static/data/salutations.json`.

### Soleil A — 12 temps
1. Montagne / mains en prière — expiration
2. Bras levés — inspiration
3. Flexion avant — expiration
4. Demi-flexion debout — inspiration
5. Planche — expiration
6. Chaturanga — expiration (genoux posés en version douce)
7. Chien tête en haut — inspiration (**Cobra en version douce**)
8. Chien tête en bas — expiration ; 3 à 5 respirations
9. Demi-flexion debout — inspiration
10. Flexion avant — expiration
11. Bras levés — inspiration
12. Montagne — expiration

### Lune — 18 temps
1. Montagne
2. Inclinaison latérale droite
3. Inclinaison latérale gauche
4. Déesse
5. Étoile à cinq branches
6. Triangle droit
7. Pyramide droite
8. Fente basse droite
9. Fente latérale droite
10. Fente latérale gauche
11. Fente basse gauche
12. Pyramide gauche
13. Triangle gauche
14. Étoile
15. Déesse
16. Inclinaison gauche
17. Inclinaison droite
18. Montagne

**Important** : la Salutation à la lune comporte plusieurs écoles et variantes, sans une unique séquence universelle. La présente variante est lente, bilatérale et adaptée d'une source documentée.

## Déverrouillage, synchronisation et intégrité

- Le profil possède des `masteredPoseStatus` horodatés : cliquer « Je maîtrise cette posture » dans chaque fiche ; **ne pas marquer une posture maîtrisée après une seule séance terminée**.
- Les deux salutations s'affichent comme parcours, avec liste cliquable des postures non encore déclarées maîtrisées.
- 8 prérequis distincts pour le soleil complet et 7 pour la version douce avec Cobra ; 8 pour la Lune. Ces validations sont synchronisées entre appareils avec résolution par date des modifications.
- `static/data/programs.json` propose maintenant un parcours pédagogique « Apprendre les salutations » en 7 étapes. Les deux séquences ne démarrent que si leurs prérequis sont complets.
- Le guidage propose les instructions à l'écran, le souffle et des clips MP3 précalculés. **Les 60 consignes Vivienne des deux salutations sont désormais présentes dans le dépôt, au sein de 183 MP3 au total** après relance réussie de la génération. Le test sur Safari iPhone réel reste une étape distincte avant validation complète.

## Audit illustrations

**48/48** fichiers PNG d'origine candidates pour le catalogue Yoga API, **13/13** pour les positions essentielles historiques.

Pour les 12 postures/mouvements supplémentaires introduits par les salutations, **12/12** PNG individuels candidats sont rassemblés dans `SichoSana_V2.3_73_illustrations_originales.zip`. Les quatre dernières images (demi-relevé, Chaturanga, inclinaison latérale, étoile) sont des retouches/compositions et leur netteté mérite une vérification sur grand écran.

- Soleil complet + adaptation : 9/9 mouvements distincts dotés d'illustration originale candidate.
- Lune : 8/8 mouvements dotés d'illustration originale candidate.
- Pour l'instant, l'application sait privilégier `/media/original/{id}.png`, puis basculer vers une source Yoga API/Wikimedia **de la même posture exacte** si le fichier original manque.
- Les originaux sont fournis dans `SichoSana_V2.3_73_illustrations_originales.zip` à importer sur le NAS, mais **ils ne sont pas contenus en binaire dans la branche GitHub**.
- Garder les crédits tiers tant que les images tierces restent visibles en repli. Ne les retirer qu'après validation de la couverture d'images propriétaires à 100 %.

## Contrôles qualité

- Tester les boutons de maîtrise, le verrouillage des salutations, l'enchaînement guidé sur iPhone/iPad/ordinateur et la synchronisation de deux profils.
- Vérifier sur iPhone réel Safari la lecture de chaque nouveau MP3 avant publication définitive, sans confusion avec les MP3 existants de yoga et méditation.
- Contrôler les postures en extension (cobra/chien tête en haut), en inversion, les changements droite/gauche, les doigts et la nuque.

Version intégrée au GitHub de développement uniquement ; **ne présume pas de déploiement sur NAS**.
