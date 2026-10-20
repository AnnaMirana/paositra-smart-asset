# PAOSITRA SMART ASSET — PROJECT_CONTEXT
Version 1.0 — Session 0 / nouveau départ

## Source de vérité
Ce document est la référence commune du projet. Toute IA doit le lire avant de proposer une architecture ou du code. Une proposition d'IA n'est pas automatiquement une décision validée.

## Projet
Nom : PAOSITRA SMART ASSET
Sous-titre de travail : Système de gestion, inventaire et traçabilité des produits.

Objectif : suivre les produits depuis leur entrée au CAM, leur stockage, leurs sorties vers les directions, leurs transferts éventuels, retours, inventaires et écarts, jusqu'à leur fin d'utilisation, avec traçabilité.

## Contexte métier établi
- CAM = Centre de stockage.
- Le stock physique est centralisé au CAM.
- DSID gère/supervise le processus de stock, l'inventaire et les mouvements.
- Les fournisseurs approvisionnent le CAM.
- Les produits arrivent au CAM et font l'objet d'une vérification/inventaire d'entrée.
- Les directions transmettent des demandes.
- Le système ne gère PAS l'acceptation administrative des demandes.
- Seules les quantités confirmées et la liste des produits à donner sont prises en compte.
- Une sortie peut contenir plusieurs produits.
- Chaque produit d'une sortie génère son propre mouvement de stock.
- Une sortie supérieure au stock disponible est bloquée.
- Après sortie, le suivi continue dans la direction destinataire.
- Un produit peut être transféré plusieurs fois entre directions.
- Un produit peut revenir vers DSID/CAM.
- Le suivi va jusqu'à la fin d'utilisation.

## DÉCISIONS VALIDÉES — NE PAS ROUVRIR SANS JUSTIFICATION
- Compatibilité produit/équipement : HORS PÉRIMÈTRE.
- Champs fiche d'entrée : produit, référence, quantité, date, origine, document.
- CODIG : concept de « fiche » lié aux sorties ; définition exacte à confirmer.
- Unité de gestion : mixte, pièce ou lot selon le type de produit.
- Une même référence peut être reçue plusieurs fois ; les quantités s'ajoutent selon les règles de stock.
- Sortie > stock disponible : BLOQUÉE.
- Pas de Demande séparée dans le système : uniquement la sortie liée à une direction, avec quantités confirmées.
- Correction : jamais de suppression. L'ancienne donnée est conservée et marquée erreur ; une nouvelle donnée correcte est enregistrée.
- Écart d'inventaire inexpliqué : alerte + quantité manquante ; ne pas inventer une sortie.
- Localisation physique du stock : CAM.
- Informations produit pouvant être complétées par la direction destinataire.
- Suivi jusqu'à fin d'utilisation.
- Traçabilité double identité : compte connecté (ex. TECH-003) ET opérateur déclaré.
- Table dédiée `Opérateur`.
- Nom de l'opérateur : saisie texte libre obligatoire à chaque opération, avec réutilisation/autocomplétion pour éviter les doublons d'orthographe.
- Les deux identités sont conservées ensemble sur chaque opération, y compris les corrections.

## Exemple de correction
Entrée initiale : 50 imprimantes.
Après inventaire : 49.
On ne supprime pas 50.
On conserve 50 comme donnée initiale erronée, puis on enregistre 49 comme valeur corrigée, avec auteur/date/motif de correction.

## Exemple d'écart
Stock théorique : 50.
Aucune sortie enregistrée.
Inventaire physique : 47.
=> alerte d'écart de -3 ; ne pas créer une sortie fictive.

## Flux métier de référence
Fournisseur → réception CAM → inventaire d'entrée → enregistrement entrée → stock central → quantités confirmées pour une direction → contrôle du stock → blocage si quantité insuffisante / sinon sortie → réception direction → utilisation ou transfert → fin d'utilisation / retour éventuel.

Le diagramme de flux existe déjà. La règle exacte de réintégration d'un retour reste À CONFIRMER.

## BLOC C — PROPOSITIONS À PRÉPARER AVANT VALIDATION PAOSITRA
1. rôles et permissions ;
2. workflow de validation ;
3. catégories/familles/types de produits ;
4. règle d'attribution des références ;
5. règle QR/code-barres.

Ces éléments sont des PROPOSITIONS, pas des faits officiels.

## Proposition QR actuelle
Un QR unique peut pointer vers un identifiant/URL stable de la fiche produit. Les données modifiables ne doivent pas être gravées directement dans le QR. Le scan affiche la fiche selon les droits. À valider avec Paositra.

## Architecture technique cible
Frontend : React.
Backend : Python + Django + Django REST Framework (DRF).
Base : PostgreSQL DÈS LE DÉVELOPPEMENT. SQLite n'est pas utilisé pour le nouveau projet.
ORM : Django ORM.
FastAPI : optionnel, seulement si une partie IA/microservice le justifie.
Git/GitHub.
Backend et frontend séparés.

Principe :
React → API HTTP → Django + DRF → Django ORM → PostgreSQL.

## Modèle de données
L'ancien modèle ACTIF → ÉVÉNEMENT → AFFECTATION/TRANSFERT/INCIDENT/MAINTENANCE est OBSOLÈTE pour le nouveau périmètre.
Le MCD doit être reconstruit à partir du nouveau métier.
Concepts à étudier, non définitifs : Produit, Catégorie/Type, Opérateur, Utilisateur/Compte, Direction/Service, Entrée, Sortie, Ligne de sortie, Stock/Localisation, Transfert, Retour, Inventaire, Écart, Correction, Document/Fiche.

## Périmètre
MUST HAVE : produits/références, entrées, stock, sorties, directions, mouvements/transferts, suivi, inventaires, écarts/alertes, corrections traçables, utilisateurs/opérateurs.
IMPORTANT : QR, dashboard, alertes améliorées, rôles/permissions détaillés.
BONUS : fonctionnalités avancées après validation du MVP.
HORS PÉRIMÈTRE : acceptation administrative des demandes, compatibilité produit/équipement, fonctionnalités non justifiées.

## Vérité des données
Ne jamais inventer une information sur Paositra.
Information inconnue : `À CONFIRMER`.
Information absente : `NC`.
Les données de test ne sont jamais présentées comme données réelles.

## Ordre de travail
1. cadrage métier ;
2. Bloc C : propositions ;
3. validation des propositions ;
4. MCD ;
5. architecture détaillée ;
6. PostgreSQL ;
7. Django + DRF ;
8. API ;
9. React ;
10. authentification/rôles ;
11. QR ;
12. dashboard/alertes ;
13. tests ;
14. documentation ;
15. soutenance.

## Méthode avec l'étudiante
Elle veut comprendre avant de coder et pouvoir défendre le projet devant un jury.
Toujours privilégier : objectif → logique métier → décision → conception → petite question de compréhension si utile → implémentation → test → ce qu'il faut retenir.
Éviter les gros blocs de code non expliqués, le jargon non expliqué et les changements silencieux.

## Gouvernance des IA
- ChatGPT : chef de projet / architecte principal / mentor.
- Claude : auditeur métier / reviewer / challenger.
- Gemini : implémentation / débogage.
- Cursor : intégration finale / tests du repository.

Toute proposition d'une IA doit être marquée PROPOSITION — À VALIDER si elle change le projet.
