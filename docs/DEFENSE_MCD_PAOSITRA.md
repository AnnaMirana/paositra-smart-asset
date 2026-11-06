# PAOSITRA SMART ASSET — préparation de défense du MCD

## 1. Position à tenir lundi

Le MCD présenté n'est pas un modèle fait au hasard par une IA.

Il a été construit à partir des informations recueillies auprès de l'encadrement, puis discuté et simplifié progressivement.

Objectif maintenant : **arrêter de refaire le cadrage en boucle et passer à la réalisation.**

Si une règle métier est réellement fausse, elle doit évidemment être corrigée. Mais une amélioration facultative ou une fonctionnalité supplémentaire ne doit pas automatiquement provoquer une refonte du MCD.

Phrase utile :

> « Je suis ouverte à corriger une règle métier qui serait réellement incorrecte. Par contre, j'aimerais qu'on distingue cela d'une amélioration possible, parce que le cadrage et le MCD ont déjà demandé plusieurs semaines et je voudrais maintenant commencer l'implémentation pour avoir un résultat fonctionnel dans les trois mois. »

---

## 2. Idée générale du projet

Le système sert à gérer les articles/matériels informatiques :

- ce qui entre au CAME ;
- ce qui est disponible en stock ;
- les demandes des directions ;
- l'autorisation et la validation ;
- les sorties réelles ;
- l'identification de chaque article physique ;
- les mouvements et l'historique ;
- les utilisateurs qui réalisent les opérations.

On garde volontairement une structure simple.

---

# 3. Les entités et pourquoi elles existent

## UTILISATEUR

Compte permettant de se connecter au système.

Attributs :
- id_utilisateur
- identifiant
- nom
- mot_de_passe
- role
- actif

Pourquoi ?

Pour savoir qui utilise le système et tracer les opérations.

---

## CATEGORIE

Regroupe les grandes familles.

Exemples :
- Ordinateur
- Souris
- Imprimante

Pourquoi ?

Pour organiser les types d'articles.

---

## TYPE_ARTICLE

Décrit le type précis.

Exemples :
- Ordinateur portable
- Ordinateur bureau
- Souris sans fil
- Souris avec fil

Attributs principaux :
- id_type
- nom
- référence
- quantité_stock

Pourquoi ?

Parce que le stock est consulté naturellement au niveau du type.

Exemple :

Souris sans fil → stock = 50.

---

## ARTICLE

Représente une unité physique précise.

Exemple :

Type = Souris sans fil

Articles :
- REF001 / QR001
- REF002 / QR002
- REF003 / QR003

Chaque article physique possède son identité propre.

Pourquoi ?

Parce que deux souris du même type ne sont pas forcément le même objet physique.

Le QR code permet de retrouver l'article et son suivi.

---

## FOURNISSEUR

Représente la source liée à une entrée.

On ne crée pas une entité DON séparée : l'origine est conservée dans ENTREE.

---

## ENTREE

Représente l'arrivée de matériel.

Attributs :
- id_entree
- date_entree
- document
- ref_entree
- origine

Une entrée peut contenir plusieurs types d'articles.

La quantité détaillée est donc dans LIGNE_ENTREE.

---

## LIGNE_ENTREE

Détail d'une entrée.

Exemple :

ENTREE 001 :
- ordinateur portable × 10
- souris sans fil × 20
- imprimante × 3

Attribut :
- quantite

Pourquoi ?

Parce qu'une seule entrée peut contenir plusieurs types.

---

## DIRECTION

Direction qui demande du matériel.

---

## BON_SORTIE

C'est la demande officielle d'une direction.

Exemple :

Direction RH demande :
- 20 laptops
- 20 souris

Le BS peut être en attente, refusé ou validé.

Il sert à gérer la demande et le processus d'autorisation/validation.

---

## LIGNE_SORTIE

Détail de la demande.

Attributs :
- quantite_demandee
- quantite_autorisee
- quantite_livree

Exemple :

Laptops :
- demandé = 20
- autorisé = 15
- livré = 15

La ligne concerne un TYPE_ARTICLE, pas un QR particulier.

---

## SORTIE

Représente la sortie physique réelle.

Elle permet de savoir ce qui a effectivement quitté le CAME.

Attributs :
- id_sortie
- date_sortie
- quantite
- document
- ref_sortie

La sortie est liée aux articles physiques réellement sortis.

---

## MOUVEMENT

Permet de conserver l'historique de l'article.

Exemples de types :
- entrée
- sortie
- retour
- réintégration
- autre mouvement nécessaire au suivi

On ne crée pas une entité HISTORIQUE séparée : l'historique est obtenu à partir des mouvements.

---

# 4. Logique des relations principales

CATEGORIE
→ TYPE_ARTICLE
→ ARTICLE

ENTREE
→ LIGNE_ENTREE
→ TYPE_ARTICLE / ARTICLE

DIRECTION
→ BON_SORTIE
→ LIGNE_SORTIE
→ TYPE_ARTICLE

BON_SORTIE
→ SORTIE
→ ARTICLE

ARTICLE
→ MOUVEMENT

UTILISATEUR
→ opérations enregistrées

---

# 5. Exemple complet à savoir expliquer

Une entrée arrive :

10 ordinateurs portables.

On crée une ENTREE.

Elle contient une LIGNE_ENTREE :

ordinateur portable = 10.

Les 10 objets physiques sont ensuite identifiés individuellement :

ART001 / QR001
ART002 / QR002
...
ART010 / QR010

Plus tard, une direction demande 5 ordinateurs portables.

On crée un BON_SORTIE.

Sa LIGNE_SORTIE indique :

demandé = 5
autorisé = 5
livré = 5

Quand les 5 ordinateurs quittent réellement le CAME, on crée la SORTIE et on identifie les 5 ARTICLES physiques concernés.

Chaque article peut ensuite être retrouvé par son QR code.

Son historique permet de voir ses mouvements.

---

# 6. Pourquoi ne pas avoir 50 autres entités ?

Parce que le but n'est pas de modéliser toute l'organisation de Paositra.

Le but est de construire une application fonctionnelle dans le temps disponible.

Donc on évite volontairement :
- entité Origine ;
- entité Historique ;
- entité Don ;
- entité Retour séparée ;
- relations directes redondantes ;
- fonctionnalités non nécessaires au MVP.

---

# 7. Plan des trois mois

## Bloc 1 — Conception terminée

- cadrage métier
- questions à l'encadrement
- règles métier
- MCD
- validation du périmètre

## Bloc 2 — Base de données

- PostgreSQL
- création du projet Django
- modèles
- migrations
- données de test

## Bloc 3 — Backend

- authentification
- utilisateurs / rôles
- catégories
- types d'articles
- articles
- entrées
- lignes d'entrée
- directions
- bons de sortie
- lignes de sortie
- sorties
- mouvements

## Bloc 4 — API

- API Django REST Framework
- consultation du stock
- création des entrées
- gestion des BS
- validation
- sorties
- historique

## Bloc 5 — Frontend

React :
- connexion
- tableau de bord
- stock
- entrées
- bons de sortie
- validation
- sorties
- articles
- historique

## Bloc 6 — QR

- génération d'un QR par article
- scan
- ouverture de la fiche article
- consultation de l'historique

## Bloc 7 — Tests

Tester notamment :

1. entrée de matériel ;
2. création automatique/identification des articles ;
3. augmentation du stock ;
4. création d'un BS ;
5. autorisation ;
6. validation ;
7. sortie réelle ;
8. diminution du stock ;
9. historique ;
10. recherche par référence / QR ;
11. retour si retenu dans le périmètre ;
12. correction d'une erreur.

## Bloc 8 — Finalisation

- sécurité minimale
- corrections
- documentation
- captures
- démonstration
- préparation soutenance

---

# 8. Règle pour lundi

Ne pas présenter le MCD comme « parfait pour toujours ».

Le présenter comme :

> « Voici le modèle retenu après le cadrage effectué. Il couvre les fonctions essentielles du projet et reste volontairement simple pour permettre une implémentation complète pendant les trois mois. »

Puis demander :

> « S'il y a une règle métier qui n'est pas correcte, je veux évidemment la corriger. Mais si c'est une amélioration ou une extension possible, je préférerais la mettre dans les évolutions plutôt que de refaire le MCD maintenant. »

C'est une position beaucoup plus solide que de dire simplement « je refuse de changer le MCD ».

