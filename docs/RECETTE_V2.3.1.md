# v2.3.1 — candidat, non déployable avant validation
Base : 4c59b0c9b66c40cbd3355a630560ba928a1ace2f. Nestor et main restent inchangés.
- P0 : image entièrement contenue, séance immersive, lecteur audio persistant, transitions automatiques, cache PWA renouvelé, nouveau pack Vivienne v3 à générer et écouter, horoscope par période avec cache daté.
- P1 : double chrono, précédent/suivant, wake lock (si compatible), étiquetage explicite de l'image cible en préparation et variante douce.
- Restent à faire : corpus de 400 réflexions originales relues, validation de la source astrologique (attribution publique et requête réelle depuis Nestor), contrôle anatomique des 58 fichiers et correspondance des variantes, génération et écoute du pack v3, script de déploiement v2.3.1 et nettoyage des sondes transitoires.
- Tests ajoutés : dimensions et transition sans geste, unicité du lecteur, calendrier astrologique. Aucun résultat de CI n'est présumé.
- Tests historiques indispensables : comptes, SQLite, profils, synchronisation, SMTP, 73 références/58 images/15 alias, 12 et 18 étapes, HTTP Range, hors ligne, iPhone/iPad/desktop, deux thèmes.
- Recette réelle Safari/iOS et PWA obligatoire : écran court, rotation, zoom texte, pause/reprise, transitions, audio hors ligne, silencieux, prononciation française, maintien écran éveillé.
