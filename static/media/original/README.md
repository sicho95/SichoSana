# Illustrations originales SichoSana v2.3

**58 PNG canoniques couvrent 73 fiches de postures** : 13 essentielles, 48 références Yoga API et 12 compléments des salutations Soleil et Lune. Le manifeste `static/data/original-art.json` contient 73 identifiants, 15 alias et 58 fichiers physiques attendus.

Les 58 PNG sont effectivement publiés. Leurs empreintes Git ont été comparées aux empreintes de l'archive fournie : aucune différence. Les alias pointent vers les fichiers canoniques, sans duplication.

Cobra (`bhujangasana`) et chien tête en haut (`urdhva-mukha`) sont distincts. La revue à taille réelle confirme une différence de position du bassin et des bras ; elle ne constitue pas une certification anatomique professionnelle. Planche et Chaturanga sont également distincts.

Contrôle technique : `python scripts/verify-v23-art-and-salutations.py --root .`. Le script QNAP télécharge le code et les PNG ensemble, sans ZIP manuel ni Git sur le NAS.
