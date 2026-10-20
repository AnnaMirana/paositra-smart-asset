# FICHE DE PRÉPARATION — DÉFENSE DU MCD
## PAOSITRA SMART ASSET
### Système de gestion, d’inventaire et de traçabilité des produits

## 1. Objectif du MCD

Le MCD représente les données nécessaires pour gérer les produits matériels depuis leur entrée au CAME jusqu’à leur sortie vers une direction, puis leur suivi dans le temps.

Il doit permettre de savoir :
- quels types de produits existent ;
- combien sont en stock ;
- quels articles physiques existent ;
- d’où viennent les matériels ;
- quelle direction demande du matériel ;
- ce qui a été demandé, autorisé et livré ;
- quels articles physiques sont réellement sortis ;
- où un article a été déplacé ;
- quel est son historique ;
- quels utilisateurs sont intervenus.

Principe central :

**TYPE_ARTICLE = type de produit**  
**ARTICLE = unité physique**  
**BON_SORTIE = demande**  
**SORTIE = sortie physique réelle**  
**MOUVEMENT = historique**

---

# 2. Les entités

## CATEGORIE
Grande famille de produits.

Attributs :
- id_categorie
- nom_categorie

Exemples : Ordinateur, Souris, Imprimante.

## TYPE_ARTICLE
Type précis de produit.

Attributs actuels :
- id_type
- nom_type_article
- quantite_stock
- reference

**Point à vérifier :** les informations métier récentes indiquent que la référence comptable est propre à chaque article physique. Il faut donc confirmer si `reference` doit rester dans TYPE_ARTICLE. La référence physique unique est actuellement `ARTICLE.ref_article`.

## ARTICLE
Un matériel physique individuel.

Attributs :
- id_article
- qr_code
- ref_article

Exemple : dix ordinateurs du même type correspondent à dix ARTICLE différents, avec chacun une référence et un QR uniques.

## FOURNISSEUR
Source/fournisseur associé à une entrée.

Attributs :
- id_fournisseur
- nom_fournisseur

## ENTREE
Arrivée de matériel au CAME.

Attributs :
- id_entree
- date_entree
- document
- ref_entree
- origine

## LIGNE_ENTREE
Détail d’une entrée.

Attributs :
- id_ligne_entree
- quantite

Elle précise le type et la quantité reçue.

## DIRECTION
Destination/service demandeur.

Attributs :
- id_direction
- nom_direction
- service

Exemple : Direction Antaninarenina / Service Finance.

## BON_SORTIE
Demande officielle d’une direction/service.

Attributs :
- id_bs
- reference_bs
- date_bs
- statut

Un BS peut contenir plusieurs types de produits.

## LIGNE_BSORTIE
Détail de la demande.

Attributs :
- id_ligne_bs
- quantite_demandee

Exemple BS001 :
- ordinateur portable : 10
- souris sans fil : 20
- imprimante : 5

## SORTIE
Opération physique réellement effectuée.

Attributs :
- id_sortie
- date_sortie
- quantite
- document
- ref_sortie

Dans le modèle actuel, un BS est exécuté une seule fois : il peut avoir zéro SORTIE avant exécution ou une SORTIE après exécution.

## LIGNE_SORTIE
Détail de la sortie réelle par type.

Attributs :
- id_ligne
- quantite_demandee
- quantite_autorisee
- quantite_livree

Exemple :
- demandée : 20 souris
- autorisée : 15
- livrée : 15

## MOUVEMENT
Historique des changements concernant un article.

Attributs :
- id_mouvement
- date_mouvement
- type_mouvement

Un article peut avoir plusieurs mouvements au cours de sa vie.

## UTILISATEUR
Compte utilisé dans le système.

Attributs :
- id_utilisateur
- identifiant
- role
- actif
- nom
- mot_de_passe

## INTERVIENT
Association entre BON_SORTIE et UTILISATEUR.

Attributs de l’association :
- role_intervention
- date_intervention

Elle permet de garder la trace des utilisateurs intervenus sur un BS.

---

# 3. Pourquoi LIGNE_BSORTIE et LIGNE_SORTIE sont toutes les deux nécessaires

C’est le point le plus important à savoir expliquer.

### LIGNE_BSORTIE
Représente **ce que la direction demande**.

### LIGNE_SORTIE
Représente **ce qui est traité lors de la sortie réelle**.

Exemple :

BS001 demande :
- 10 ordinateurs
- 20 souris
- 5 imprimantes

Après contrôle :
- ordinateurs : 10 autorisés
- souris : 15 autorisées
- imprimantes : 5 autorisées

La LIGNE_SORTIE conserve alors, pour chaque type :
- quantité demandée ;
- quantité autorisée ;
- quantité livrée.

Enfin, ARTICLE identifie les unités physiques réellement sorties.

Donc :

**LIGNE_BSORTIE = demande par type**  
**LIGNE_SORTIE = réalisation par type**  
**ARTICLE = identification physique de chaque unité**

Il ne s’agit pas de gérer des livraisons partielles : un BS est exécuté une seule fois dans le modèle actuel.

---

# 4. Les associations et cardinalités

## CATEGORIE — TYPE_ARTICLE
**CATEGORIE (1,n) — TYPE_ARTICLE (1,1)**

Une catégorie possède plusieurs types ; un type appartient à une seule catégorie.

## TYPE_ARTICLE — ARTICLE
**TYPE_ARTICLE (0,n) — ARTICLE (1,1)**

Un type peut avoir plusieurs articles physiques ; un article correspond à un seul type.

## FOURNISSEUR — ENTREE
**FOURNISSEUR (0,n) — ENTREE (1,1)**

Un fournisseur peut être associé à plusieurs entrées ; une entrée est actuellement rattachée à un fournisseur.

**À confirmer :** traitement d’une entrée provenant d’un don sans fournisseur.

## ENTREE — LIGNE_ENTREE
**ENTREE (1,n) — LIGNE_ENTREE (1,1)**

Une entrée contient une ou plusieurs lignes ; chaque ligne appartient à une entrée.

## LIGNE_ENTREE — TYPE_ARTICLE
**LIGNE_ENTREE (1,1) — TYPE_ARTICLE (0,n)**

Une ligne concerne un type ; un type peut apparaître dans plusieurs entrées.

## LIGNE_ENTREE — ARTICLE
Dans le schéma actuel :
**LIGNE_ENTREE (1,1) — ARTICLE (0,n)**

**Point à vérifier :** si un article physique possède une seule entrée d’origine, le `(0,n)` côté ARTICLE mérite d’être revu. Ne pas le modifier sans validation métier.

## TYPE_ARTICLE — LIGNE_BSORTIE
**TYPE_ARTICLE (0,n) — LIGNE_BSORTIE (1,1)**

Un type peut être demandé dans plusieurs BS ; une ligne de demande concerne un seul type.

## BON_SORTIE — LIGNE_BSORTIE
**BON_SORTIE (1,n) — LIGNE_BSORTIE (1,1)**

Un BS contient plusieurs lignes ; une ligne appartient à un seul BS.

## TYPE_ARTICLE — LIGNE_SORTIE
**TYPE_ARTICLE (0,n) — LIGNE_SORTIE (1,1)**

Un type peut apparaître dans plusieurs sorties ; une ligne concerne un seul type.

## SORTIE — LIGNE_SORTIE
**SORTIE (1,n) — LIGNE_SORTIE (1,1)**

Une sortie contient une ou plusieurs lignes ; une ligne appartient à une seule sortie.

## BON_SORTIE — SORTIE
**BON_SORTIE (0,1) — SORTIE (1,1)**

Un BS peut exister avant sa sortie physique ; lorsqu’une sortie existe, elle correspond à un seul BS.

Dans le modèle métier actuel, un BS n’est exécuté qu’une seule fois.

## SORTIE — ARTICLE
**SORTIE (1,n) — ARTICLE (0,n)**

Une sortie concerne plusieurs articles physiques. Un article peut apparaître dans plusieurs sorties au cours de sa vie s’il est retourné puis ressorti.

## ARTICLE — MOUVEMENT
**ARTICLE (0,n) — MOUVEMENT (1,1)**

Un article peut avoir plusieurs mouvements ; chaque mouvement concerne un seul article.

## BON_SORTIE — UTILISATEUR via INTERVIENT
**BON_SORTIE (1,n) — INTERVIENT — UTILISATEUR (0,n)**

Plusieurs utilisateurs peuvent intervenir sur un BS et un utilisateur peut intervenir sur plusieurs BS.

`role_intervention` et `date_intervention` appartiennent à l’association car ils décrivent l’intervention.

## DIRECTION — BON_SORTIE
**DIRECTION (0,n) — BON_SORTIE (1,1)**

Une direction peut faire plusieurs demandes ; un BS appartient à une seule direction/service demandeur.

## MOUVEMENT — DIRECTION
Dans le schéma actuel :
**MOUVEMENT (1,1) — DIRECTION (0,n)**

**Point à confirmer :** cette cardinalité signifie que chaque mouvement doit obligatoirement avoir une direction. Cela peut poser question pour une entrée au CAME ou certains retours. Si DIRECTION représente uniquement la destination d’un mouvement, le côté MOUVEMENT pourrait devoir être facultatif selon les types de mouvement. À valider avant de figer.

---

# 5. Exemple complet à raconter au jury

> Une direction demande 10 ordinateurs et 20 souris. Le Bon de Sortie est enregistré. Les deux demandes deviennent deux lignes dans LIGNE_BSORTIE. Le DSID vérifie le stock et peut autoriser, par exemple, 10 ordinateurs et seulement 15 souris. Après validation, une SORTIE est créée. Ses LIGNE_SORTIE indiquent les quantités demandées, autorisées et livrées. Enfin, les articles physiques réellement sortis sont identifiés individuellement grâce à leur référence et leur QR code. Les mouvements permettront ensuite de suivre leur historique.

---

# 6. Questions probables du jury

### Pourquoi avoir créé LIGNE_BSORTIE ?
Parce qu’un BS peut contenir plusieurs types de matériels. Elle permet de détailler chaque demande et sa quantité.

### Pourquoi avoir aussi LIGNE_SORTIE ?
Parce que la demande et la sortie physique sont deux étapes différentes. Elle conserve les quantités demandées, autorisées et livrées.

### Pourquoi ne pas mettre la quantité directement dans BON_SORTIE ?
Parce qu’un BS peut contenir plusieurs types avec des quantités différentes. La quantité appartient donc au détail de la demande.

### Pourquoi TYPE_ARTICLE et ARTICLE sont séparés ?
TYPE_ARTICLE représente le produit ; ARTICLE représente une unité physique précise.

### Pourquoi un QR par ARTICLE ?
Pour identifier chaque unité physique et retrouver son historique.

### Pourquoi MOUVEMENT ?
Parce qu’un article peut changer de situation plusieurs fois. MOUVEMENT conserve l’historique.

### Pourquoi ne pas créer HISTORIQUE ?
MOUVEMENT représente directement les événements. Une entité HISTORIQUE séparée ferait doublon.

### Pourquoi BON_SORTIE et SORTIE sont séparés ?
BON_SORTIE représente la demande administrative ; SORTIE représente l’opération physique réalisée.

### Pourquoi DIRECTION est reliée à BON_SORTIE ?
Parce que le BS est émis par une direction/service demandeur.

### Pourquoi INTERVIENT est une association avec des attributs ?
Parce que le rôle et la date concernent l’intervention d’un utilisateur sur un BS, pas l’utilisateur seul.

---

# 7. Les 13 choses à retenir

1. CATEGORIE = grande famille.
2. TYPE_ARTICLE = type précis.
3. ARTICLE = unité physique.
4. ENTREE = arrivée du matériel.
5. LIGNE_ENTREE = détail d’une entrée.
6. BON_SORTIE = demande.
7. LIGNE_BSORTIE = détail de la demande.
8. SORTIE = sortie physique.
9. LIGNE_SORTIE = détail de la sortie.
10. MOUVEMENT = historique.
11. DIRECTION = service/destination demandeur.
12. UTILISATEUR = compte système.
13. INTERVIENT = trace des interventions sur un BS.

Phrase clé :

**Demande ≠ sortie réelle ≠ article physique.**

---

# 8. Points à confirmer avant de présenter le MCD comme définitivement figé

1. `reference` dans TYPE_ARTICLE : confirmer si elle est réellement nécessaire, puisque la référence physique semble être `ARTICLE.ref_article`.
2. `LIGNE_ENTREE — ARTICLE` : confirmer qu’un article physique ne provient que d’une seule ligne d’entrée.
3. `MOUVEMENT — DIRECTION` : confirmer si tous les mouvements ont obligatoirement une direction.
4. `FOURNISSEUR — ENTREE` : confirmer le cas des dons.

Ces points sont des **points à confirmer**, pas une raison pour refaire tout le modèle.

---

# 9. Conclusion orale possible

> Le modèle a été construit autour de la traçabilité du matériel. J’ai séparé le type d’article de l’article physique, puis la demande de sortie de la sortie réellement effectuée. Les mouvements permettent ensuite de conserver l’historique des articles. L’objectif était de garder un modèle suffisamment simple pour couvrir le processus métier sans ajouter des entités qui ne sont pas nécessaires.
