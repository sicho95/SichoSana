# Illustrations originales SichoSana v2.3 — 58 assets, 73 fiches

Le répertoire contient **58 fichiers PNG canoniques**, correspondant à **73 fiches** :
13 postures essentielles, 48 postures Yoga API et 12 postures/transitions pour les salutations.

Le manifeste `static/data/original-art.json` définit `files` (73 IDs),
`aliases` (15 correspondances vers un PNG existant) et `expectedPhysicalFiles` (58).

Chaque fiche utilise `/media/original/<id-canonique>.png` ; les alias ne
nécessitent **aucune copie de fichier physique**. Cobra (`bhujangasana`) et
chien tête en haut (`urdhva-mukha`) restent distincts, tout comme planche
(`phalakasana`) et planche basse (`chaturanga`).

Les 58 PNG **ne sont pas encore publiés**. Tant que la publication n'est pas
complète, le déploiement QNAP bloque et la CI doit échouer.

Publier les illustrations depuis le ZIP initial validé :
`scripts/publish-v23-original-art-github.py /chemin/vers/73_images.zip`.
Ce script vérifie les 73 fichiers du ZIP, les 15 identités binaires, puis
n'envoie que les 58 originaux et produit un unique commit.

**Contrôle humain nécessaire** : l'illustration actuelle du chien tête en haut
semble garder les cuisses au sol ; vérifier/corriger ce visuel avant
validation anatomique et déploiement de production.
