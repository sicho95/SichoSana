# Recette v2.3.1 — branche candidate, ne pas déployer sans validation
Référence préservée : 4c59b0c9b66c40cbd3355a630560ba928a1ace2f. Nestor et main restent inchangés.
| Correction | Contrôle attendu |
|---|---|
| Image entière | object-fit contain, boîte bornée, revue des 58 PNG et 15 alias sur écran |
| Séance immersive | commandes visibles à 390×664, iPad et bureau, deux chronos |
| Automatisme voix | un seul élément audio, transition sans geste, écoute iPhone réelle |
| Accent français | nouveau contexte narratif, même Vivienne, 183 MP3 vérifiés et écoute humaine |
| Cache | pack v3 distinct, 58 images et 183 MP3 téléchargeables, test hors ligne réel |
| Horoscope | deux phrases de la source, période et cache datés, panne non masquée ; vérifier autorisation Sigastra |
| Réflexion | 400 phrases distinctes, permutation stable par profil, relecture éditoriale |
| Précédente/suivante | navigation et reprise sans perte de session |
| Éveil écran | Wake Lock si compatible, libéré à pause/fin |
| Préparation/douce | image cible explicitement signalée ; variantes anatomiques à contrôler |
| Installateur | archive SHA explicite, vérifications avant application, sauvegarde SQLite et rollback |
Les résultats de CI ne sont jamais présumés. Safari réel, PWA, écoute, vérification anatomique et source réelle depuis Nestor restent des portes manuelles.

## Recette r2
- Version UI/build et serveur dans Profil et Administration ; signaler les écarts de cache.
- Bloquer zoom tactile, double tap et zoom de focus iOS, conserver le défilement. Test iPhone réel nécessaire.
- Première CI : 183 MP3 vérifiés, 23 tests Python réussis, 9 tests Chromium historiques réussis ; 2 nouveaux tests bloqués à la connexion. Suites isolées sans désactiver la limitation de production.
- Horoscope : diagnostiquer refus fournisseur, limite, réseau et réponse invalide ; nouvelle tentative. Diagnostic réel en CI et sur Nestor avant validation. Clé partenaire éventuelle côté serveur.

## Recette r3 — une posture par étape
- Les préparations restent pédagogiques dans les fiches. Une séance ordinaire contient exactement les occurrences prévues par le catalogue, jamais trois versions successives imposées.
- Mode adaptatif (identifiant historique initiation) : douce si non acquise, normale si acquise. Doux : douce privilégiée. Normal : complète sauf adaptation douce explicitement mémorisée. Un retour volontaire à normale ou une déclaration de maîtrise annule l'adaptation.
- Bascule durant la séance : même étape et même budget temporel, clip correspondant, préférence horodatée persistante par profil et synchronisée ; historique des variantes pratiquées. Les salutations gardent leurs prérequis et leurs 12/18 étapes ; pas de bascule complète si les prérequis complets manquent.
- Contrôler la séance Éveil du matin, le retour à la même étape, la navigation suivante, la persistance et la version douce ; tests sur Chromium/WebKit. Les illustrations spécifiques des variantes et les consignes différenciées de certaines salutations restent à revoir.

## r4 — transitions et apprentissage
- 19 liaisons contextualisées, deux consignes par destination selon variante ; durée incluse dans la prochaine posture, compteur inchangé, anticipation à 8 s. Salutations : consignes existantes avec phase de transition intégrée.
- Apprentissage guidé séparé pour les 13 fiches pédagogiques : préparation, variante douce, version complète/respiration/alignement/précautions ; fin sans validation automatique ni ajout à l'historique des séances.
- Pack Vivienne v4 attendu : 234 clips et durée réelle mesurée ; cache versionné. Les images intermédiaires spécifiques restent à produire si la recette pédagogique les identifie comme indispensables.
- Recette : couverture des liaisons, chronomètres, aperçu, phase vocale, apprentissage, non-régression. Écoute et essais anatomiques réels encore nécessaires.

## r5 — finition
- Aperçu de la prochaine posture avec miniature originale ; consignes distinctes pour le cobra et le chien tête en haut, la planche basse et son adaptation. Test de couverture du catalogue et des deux variantes de la salutation.
- Vérification directe du moteur r4 : 50 cas (25 transitions dans les séances × 2 variantes) réussis, passage transition/maintien et durée totale conservée. Recette r5 complète non encore attestée.

## r6 — retour utilisateur Nestor
- Nom sanskrit puis français à l'entrée, transition contextualisée ; maintien sans réannonce ni répétition des gestes. 26 nouvelles consignes de maintien, pack Vivienne v5 (260 MP3). Noms sanskrits visibles, graphie savante conservée ; translittération TTS à écouter sur appareil réel.
- Cache CDN : app shell/data no-store, URL JS/CSS versionnées, installation SW avec reload, build API r6.
- Horoscope : capture Nestor signale explicitement configuration désactivée. Activer SICHOSANA_ASTRO_ENABLED=1 dans la configuration locale et vérifier les trois périodes dans le conteneur. Ne pas écraser la configuration NAS.
- Les illustrations des variantes restent à produire ; l'illustration de la posture cible n'est pas un visuel exact de la version douce.

## r7 — cohérence texte/illustration
- Relecture des 13 postures pédagogiques et 19 transitions. Chien tête en bas au sol en variante douce (genoux fléchis), pas de mur dans le guidage de séance. Repos après quelques respirations, alternance volontaire des côtés pour les postures asymétriques. Cobra sur les paumes, pas les avant-bras ; guerrier bras ouverts, papillon plantes jointes, torsion une jambe, savasana sur le dos avec supports facultatifs.
- Références chien tête en bas : https://www.mayoclinic.org/healthy-lifestyle/stress-management/multimedia/downward-facing-dog/vid-20453582 ; https://www.yogajournal.com/poses/downward-facing-dog/ ; https://health.clevelandclinic.org/downward-dog-adho-mukha-svanasana (adaptation mur distincte).
- Les PNG des variantes spécifiques ne sont pas créés dans cette révision. Revue visuelle exhaustive des 58 images et validation par enseignant de yoga non effectuées. Ne pas assimiler durée d'étape et maintien continu. Recette automatisée et écoute à refaire.
