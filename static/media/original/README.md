# Illustrations originales SichoSana v2.3

Ce dossier doit contenir **73 fichiers PNG distincts** portant exactement les noms
énumérés dans `static/data/original-art.json` :

- 13 postures essentielles ;
- 48 postures Yoga API ;
- 12 postures/transitions complémentaires pour les salutations.

Les fichiers binaires **ne sont pas encore publiés ici**. L'archive des originaux
mentionnée dans les notes de livraison n'est pas accessible en octets dans
l'environnement de publication actuel. Il est interdit de déclarer la v2.3
complète uniquement parce que les 73 noms apparaissent dans le manifeste.

Lors de la publication, conserver impérativement ces chemins :

`static/media/original/<id-de-posture>.png`

Une fois les 73 originaux réellement présents dans cette branche, le précontrôle
`scripts/verify-v23-art-and-salutations.py --root .` doit réussir et le
déploiement QNAP doit extraire toutes les illustrations depuis **la même archive
GitHub que le code**. La revue visuelle anatomique reste indispensable.
