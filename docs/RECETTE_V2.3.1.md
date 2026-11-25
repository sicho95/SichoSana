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
