# PAOSITRA SMART ASSET
## PROJECT_CONCEPT — Document de référence du projet
### Système de gestion, d’inventaire et de traçabilité des produits

**Version : 1.0 — Cadrage métier consolidé**  
**Date : 14 septembre 2026**  
**Statut : Base de référence pour la conception et le développement**

---

# 0. À QUOI SERT CE DOCUMENT ?

Ce document est la nouvelle base de compréhension de **PAOSITRA SMART ASSET**.

Il a deux objectifs :

1. permettre à une personne non informaticienne de comprendre clairement **le problème, le fonctionnement et ce que le système doit apporter** ;
2. permettre à un informaticien de comprendre **le périmètre fonctionnel, les règles métier, les données à modéliser, l’architecture cible et le plan de réalisation sur 3 mois**.

Ce document doit être utilisé avant toute conception technique importante.

### Règles de lecture

- **VALIDÉ / DÉFINITIF** : décision métier retenue.
- **PROPOSITION TECHNIQUE** : choix de conception que l’équipe peut faire pour réaliser le système.
- **À CONFIRMER** : information dépendant encore de Paositra.
- **NC** : non communiqué.

Aucune proposition technique ne doit être présentée comme une règle réelle de Paositra sans validation.

---

# PARTIE A — VERSION COMPRÉHENSIBLE PAR TOUT LE MONDE

# 1. LE PROJET EN UNE PHRASE

**PAOSITRA SMART ASSET est une application permettant à Paositra de gérer, suivre, inventorier et tracer les produits depuis leur arrivée au CAME jusqu’à leur sortie, leur transfert, leur éventuel retour et leur fin d’utilisation.**

L’idée centrale est simple :

> **Savoir quels produits existent, combien sont disponibles, où ils sont, qui les reçoit ou les détient, quels mouvements ont eu lieu et conserver une histoire fiable de ces mouvements.**

---

# 2. LE PROBLÈME AUQUEL LE SYSTÈME RÉPOND

La gestion des produits ne consiste pas uniquement à connaître une quantité en stock.

Il faut également pouvoir répondre à des questions comme :

- Quel produit est entré ?
- Quand est-il entré ?
- Quelle quantité est entrée ?
- D’où vient-il ?
- Quel document accompagne l’entrée ?
- Quelle quantité a été autorisée pour une sortie ?
- Quelle quantité a réellement été sortie ?
- Pour quelle direction ?
- Qui a effectué ou enregistré l’opération ?
- Quelle validation a été donnée ?
- Un produit a-t-il été transféré ?
- Est-il revenu ?
- Est-il encore utilisable ?
- Y a-t-il un écart entre le stock théorique et le stock physique ?
- Pourquoi une donnée a-t-elle été corrigée ?
- Qui a fait la correction ?
- Que s’est-il passé avant et après ?

Le système doit donc fournir une **mémoire fiable du cycle de vie des produits**.

---

# 3. LE RÔLE DU CAME

Le **CAME** signifie :

> **Centre d’Approvisionnement en Matériels et Equipements**

Le stock physique central est situé au CAME.

Le CAME intervient notamment lorsque les produits validés doivent être effectivement fournis.

Le projet doit donc utiliser **CAME** et non « CAM » dans les documents officiels du projet.

---

# 4. LES PRINCIPAUX ACTEURS

Les rôles métier identifiés sont :

## Administrateur

Il dispose des droits d’administration du système.

## Agent DSID

Il intervient notamment pour :

- saisir les informations d’entrée et de sortie ;
- consulter le stock ;
- autoriser les quantités ;
- consulter l’historique ;
- participer au suivi des opérations.

## Agent de validation

Il consulte notamment :

- le stock ;
- l’historique ;

et valide ou rejette les opérations qui lui sont soumises.

## Agent CAME

Il intervient lors de la sortie physique des produits.

Il indique notamment :

- les quantités réellement délivrées pour chaque article.

## Demandeur

Il émet le **Bon de Sortie (BS)** et intervient dans la réception des produits.

## Agent d’une direction destinataire

Il représente la destination du produit dans le circuit métier lorsque cela est nécessaire.

## Auditeur

Il dispose principalement de droits de consultation et intervient notamment dans le traitement des écarts d’inventaire.

> Les permissions exactes seront traduites dans le système à partir de ces responsabilités métier.

---

# 5. LE FONCTIONNEMENT GLOBAL

Le fonctionnement peut être résumé ainsi :

**Fournisseur**
→ **CAME**
→ **entrée et contrôle**
→ **stock**
→ **Bon de Sortie**
→ **contrôle / autorisation DSID**
→ **validation**
→ **sortie physique CAME**
→ **direction destinataire**
→ **utilisation / transfert éventuel**
→ **retour éventuel**
→ **fin d’utilisation**

Chaque étape importante doit laisser une trace dans le système.

---

# 6. L’ENTRÉE D’UN PRODUIT

Lorsqu’un produit arrive au CAME, l’entrée doit être enregistrée.

Les informations prévues comprennent notamment :

- produit ;
- référence ;
- quantité ;
- date ;
- origine ;
- document associé.

L’entrée augmente le stock selon les règles de gestion définies.

Une même référence peut être reçue plusieurs fois.

Les quantités correspondantes peuvent donc s’ajouter au stock.

---

# 7. LES PRODUITS ET LEUR ORGANISATION

Le système doit permettre d’organiser les produits avec une structure simple :

**Catégorie → Type de produit**

Exemples :

- Informatique → Imprimante
- Informatique → Ordinateur
- Fournitures → Ramette papier
- Mobilier → Bureau

La liste des catégories et des types **ne doit pas être figée dans le code**.

Elle doit pouvoir être définie/configurée dans le système.

---

# 8. PIÈCE OU LOT

La gestion est mixte :

- certains produits sont gérés à la **pièce** ;
- d’autres sont gérés au **lot** selon leur type.

Cette règle doit être intégrée au modèle de données afin d’éviter des incohérences.

---

# 9. LA RÉFÉRENCE

À ce jour, Paositra n’a pas fourni de référence existante à reprendre.

Le format de référence reste donc un **choix à définir**.

Important :

> Nous ne devons pas inventer une prétendue référence officielle Paositra.

Le système pourra proposer un format interne cohérent, mais ce format devra être considéré comme une **décision de conception**, et non comme une règle métier existante, tant qu’il n’est pas officiellement validé.

---

# 10. LE BON DE SORTIE (BS)

Le processus réel transmis par l’encadreur est le suivant :

### Étape 1 — Le demandeur

Le demandeur émet un **Bon de Sortie (BS)** contenant le nombre demandé pour chaque article.

Le document physique reste utile.

### Étape 2 — La DSID

La DSID consulte le stock et décide :

- d’autoriser la quantité demandée ;
- d’autoriser une quantité différente ;
- ou de refuser.

Un motif de refus peut être indiqué.

La décision est signée.

Ces informations doivent être saisies dans le système.

### Étape 3 — Deuxième instance

Une deuxième instance valide ou rejette le BS.

La validation est enregistrée avec l’utilisateur concerné.

### Étape 4 — CAME

Si le BS est validé, il est présenté au CAME.

Le CAME fournit les produits.

L’agent CAME enregistre alors les **quantités réellement délivrées pour chaque article**.

C’est une distinction essentielle :

> **quantité autorisée ≠ quantité réellement sortie.**

### Étape 5 — Transmission au demandeur

Les produits sont envoyés au demandeur avec un **Soit Transmis (ST)**.

Le demandeur signe le ST et le retourne à la DSID.

---

# 11. CE QUE LE SYSTÈME FAIT ET NE FAIT PAS

Le système doit numériser et tracer le processus opérationnel.

Il ne doit pas prétendre remplacer toutes les procédures administratives de Paositra.

En particulier :

- le BS physique reste utile ;
- le système enregistre les informations du BS ;
- la DSID saisit l’autorisation ;
- la deuxième instance valide ou rejette dans la plateforme ;
- le CAME enregistre la quantité réellement sortie ;
- les acteurs concernés sont notifiés.

Le système devient donc une **couche numérique de suivi, de contrôle et de traçabilité du processus réel**.

---

# 12. LE STOCK

Le système doit permettre de connaître le stock disponible.

Règle importante :

> **Une sortie supérieure au stock disponible doit être bloquée.**

Le système ne doit jamais autoriser une sortie impossible à couvrir par le stock disponible.

Le stock doit tenir compte des mouvements enregistrés.

---

# 13. LES MOUVEMENTS APRÈS LA SORTIE

Le suivi ne s’arrête pas lorsque le produit quitte le CAME.

Le système doit pouvoir suivre :

- la destination ;
- l’utilisation ;
- les transferts entre directions ;
- les retours ;
- la fin d’utilisation.

Un produit peut donc changer de direction plusieurs fois.

L’objectif est de conserver une **traçabilité chronologique**.

---

# 14. LE RETOUR D’UN PRODUIT

Un produit peut revenir vers le CAME / DSID.

Un retour doit être enregistré.

Mais un retour physique ne doit pas automatiquement augmenter le stock disponible.

Le produit doit d’abord être contrôlé.

Deux grands cas peuvent ensuite être traités :

- produit utilisable → réintégration au stock ;
- produit endommagé / hors d’usage → traitement adapté.

Cette règle évite de considérer comme disponible un produit qui vient simplement d’être retourné mais dont l’état n’a pas encore été vérifié.

---

# 15. L’INVENTAIRE

Le système doit comparer :

**stock théorique**

avec

**stock physique réellement constaté**.

Exemple :

- stock théorique : 50 ;
- aucune sortie enregistrée supplémentaire ;
- inventaire physique : 47.

Le système signale :

> **Écart : -3**

Il ne doit surtout pas inventer une sortie de 3 pour expliquer automatiquement la différence.

---

# 16. LE TRAITEMENT D’UN ÉCART

Un écart doit pouvoir être suivi.

Principe proposé :

**détecté → investigation → traitement/justification → validation/clôture**

La Direction de l’Audit doit être impliquée dans le traitement des écarts.

Le détail des responsabilités de clôture sera traduit dans les permissions du système.

---

# 17. LES CORRECTIONS

Une règle fondamentale est retenue :

> **Aucune suppression définitive d’une donnée métier importante.**

Si une donnée est incorrecte :

1. l’ancienne donnée est conservée ;
2. elle est marquée comme erronée / corrigée ;
3. une nouvelle donnée correcte est enregistrée ;
4. la correction doit être traçable ;
5. le motif et l’auteur de la correction doivent être conservés selon les droits prévus.

Cela permet de conserver la mémoire du système.

---

# 18. LA FIN D’UTILISATION

Le suivi continue jusqu’à la fin d’utilisation du produit.

Les réponses métier reçues indiquent notamment :

- une perte est déclarée perdue après investigation ;
- un produit définitivement hors service est bien considéré comme arrivé en fin d’utilisation ;
- un retour au CAME n’est pas considéré comme une fin d’utilisation ;
- le produit doit rester dans l’historique ;
- à un certain moment, il pourra être désactivé ;
- la mise hors service doit être constatée par un technicien ;
- elle doit être validée par quelqu’un de la DSI.

Le système doit donc distinguer :

> **produit encore actif / produit en fin d’utilisation / produit désactivé**

sans effacer son historique.

---

# 19. LE QR CODE

Le principe retenu est :

> **Un QR par article.**

À ce stade, le QR doit être conçu comme un identifiant stable permettant de retrouver la fiche correspondante.

Le QR ne doit pas contenir toutes les informations métier directement.

Ainsi, si les informations changent dans la base, le QR n’a pas besoin d’être réimprimé.

Le scan pourra afficher la fiche du produit selon les droits de l’utilisateur.

Le projet devra toutefois préciser techniquement la notion exacte d’« article » dans le modèle de données.

---

# 20. LES COMPTES UTILISATEURS — DÉCISION DÉFINITIVE

Cette décision est maintenant **DÉFINITIVE**.

Chaque compte possède :

- un identifiant de connexion ;
- un nom associé ;
- un rôle ;
- un mot de passe sécurisé ;
- un état actif/inactif.

Lorsqu’une personne se connecte, le système connaît le **compte utilisé**, son **nom associé** et son **rôle**.

Chaque opération réalisée dans le système est automatiquement rattachée au compte connecté.

Exemple :

**Compte : TECH-003**  
**Nom associé : M. X**  
**Rôle : Agent DSID**

Lorsque ce compte enregistre une opération, le système conserve automatiquement l’identité du compte utilisé.

Le système ne peut pas savoir avec certitude quelle personne physique a tapé le mot de passe si un identifiant est partagé.

La responsabilité de la gestion et de la protection des identifiants relève donc des règles de sécurité internes de Paositra.

Nous n’avons donc **pas besoin d’un champ “opérateur déclaré” séparé demandé à chaque opération**, sauf nouveau besoin métier explicite.

---

# 21. LA VISION DU PROJET

Le système doit permettre de passer de :

> **« Nous avons des produits et des documents »**

à :

> **« Nous avons une vision structurée, historique et traçable des produits et de leurs mouvements. »**

La logique globale est :

# ENREGISTRER → CONTRÔLER → SUIVRE → INVENTORIER → TRACER → ALERTER → DÉCIDER

---

# PARTIE B — VERSION POUR INFORMATICIENS

# 22. OBJECTIF FONCTIONNEL

Construire une application web permettant la gestion et la traçabilité du cycle de vie des produits :

**réception → entrée en stock → demande/BS → autorisation DSID → validation → sortie effective CAME → destination → transferts → retour éventuel → contrôle → réintégration ou traitement → fin d’utilisation.**

Le système doit assurer :

- intégrité du stock ;
- traçabilité des mouvements ;
- séparation des responsabilités ;
- historique ;
- gestion des corrections ;
- inventaire ;
- gestion des écarts ;
- authentification et autorisation ;
- QR par article ;
- notifications ;
- consultation adaptée au rôle.

---

# 23. ACTEURS ET PERMISSIONS CIBLES

## ADMINISTRATEUR

Droits d’administration :

- gestion des comptes ;
- gestion des rôles/permissions ;
- paramétrage ;
- consultation globale ;
- supervision.

## AGENT DSID

- créer/enregistrer les entrées ;
- saisir les informations de BS ;
- consulter le stock ;
- autoriser/refuser ;
- définir les quantités autorisées ;
- consulter l’historique ;
- suivre les mouvements ;
- consulter les écarts selon permissions.

## AGENT VALIDATION

- consulter ;
- vérifier ;
- valider/rejeter les BS ;
- consulter l’historique.

## AGENT CAME

- consulter les BS validés qui le concernent ;
- enregistrer les quantités réellement sorties ;
- finaliser l’opération physique côté CAME.

## DEMANDEUR

- émettre/saisir les informations nécessaires au BS selon le périmètre retenu ;
- suivre l’état ;
- confirmer la réception selon le flux retenu.

## AGENT DIRECTION DESTINATAIRE

- consulter les produits relevant de sa direction ;
- suivre les mouvements qui la concernent ;
- participer aux opérations de transfert/réception selon permissions.

## AUDITEUR

- consultation ;
- accès aux historiques et écarts ;
- participation au contrôle des écarts selon règles validées.

---

# 24. WORKFLOW TECHNIQUE CIBLE

## 24.1 Bon de Sortie

Flux :

```text
BS créé
   ↓
Saisie DSID
   ↓
Autorisation DSID
   ├── Refus → notification DSID / état refusé
   │
   └── Autorisé
          ↓
     Validation 2e instance
          ├── Rejet → notification DSID
          │
          └── Validé
                 ↓
              CAME
                 ↓
      Quantité réellement délivrée
                 ↓
        Sortie effective
                 ↓
        Direction destinataire
                 ↓
             ST signé
                 ↓
          Suivi / historique
```

Le modèle doit impérativement distinguer :

- quantité demandée ;
- quantité autorisée ;
- quantité réellement sortie.

---

# 25. MODÈLE CONCEPTUEL À CONSTRUIRE

Le MCD devra être reconstruit à partir du présent cadrage.

Les anciens modèles basés sur :

**ACTIF → ÉVÉNEMENT → AFFECTATION / TRANSFERT / INCIDENT / MAINTENANCE**

sont **OBSOLETES pour ce projet actuel**.

Le cœur métier actuel est le **produit et son cycle de mouvements de stock et de détention**.

Le MCD devra notamment couvrir les concepts suivants :

- Utilisateur / Compte ;
- Rôle ;
- Catégorie ;
- Type de produit ;
- Produit ;
- Référence ;
- Entrée ;
- Ligne d’entrée ;
- Bon de Sortie ;
- Ligne de BS ;
- Autorisation DSID ;
- Validation ;
- Sortie effective ;
- Direction ;
- Mouvement / transfert ;
- Retour ;
- Contrôle de retour ;
- Inventaire ;
- Écart ;
- Correction ;
- Document ;
- QR / identifiant de traçabilité ;
- fin d’utilisation / statut de cycle de vie.

Le nombre exact d’entités et les associations seront déterminés pendant la conception MERISE.

---

# 26. PRINCIPE IMPORTANT : DOCUMENT VS DONNÉE MÉTIER

Le système doit conserver la trace des documents utilisés dans le processus.

Exemples :

- document d’entrée ;
- Bon de Sortie ;
- Soit Transmis ;
- justificatif de correction ;
- document d’inventaire.

Un document n’est pas nécessairement une entité métier indépendante dans tous les cas.

La modélisation devra éviter de créer des tables uniquement parce qu’un document papier existe.

---

# 27. STOCK : RÈGLE D’INTÉGRITÉ

La disponibilité doit être calculée à partir des mouvements métier validés.

Principe :

```text
Stock disponible
=
Entrées validées
- Sorties effectives
+ Retours réintégrés
± autres mouvements validés
```

Un retour en attente de contrôle ne doit pas être automatiquement inclus dans le stock disponible.

Une sortie doit être bloquée si :

```text
quantité réellement demandée / à sortir > quantité disponible
```

Le contrôle doit être effectué côté backend et non uniquement dans l’interface React.

---

# 28. TRAÇABILITÉ

Chaque opération sensible doit conserver au minimum :

- compte utilisateur ;
- date/heure ;
- action ;
- objet concerné ;
- résultat/statut.

Pour les corrections :

- ancienne valeur ;
- nouvelle valeur ;
- motif ;
- auteur ;
- date/heure.

Le journal doit être conçu pour être exploitable pendant un audit.

---

# 29. AUTHENTIFICATION

Architecture cible :

```text
Utilisateur
 ├── identifiant
 ├── nom associé
 ├── mot de passe sécurisé
 ├── rôle
 └── statut actif/inactif
```

À chaque action métier :

```text
action → utilisateur connecté → historique/audit
```

Il ne faut pas demander manuellement le nom de l’opérateur à chaque opération.

Le compte connecté est la référence technique de traçabilité.

---

# 30. CATÉGORIES / TYPES

Structure cible :

```text
Catégorie
   └── Type de produit
          └── Produit / référence
```

Les catégories et types doivent être configurables.

L’unité de gestion doit être compatible avec le type :

```text
PIÈCE
ou
LOT
```

La règle doit être contrôlée côté backend afin d’éviter les incohérences.

---

# 31. RÉFÉRENCE ET IDENTIFIANT DE TRAÇABILITÉ

Il faut distinguer :

### Référence produit

Identifie le produit ou la référence métier.

### Identifiant de traçabilité

Identifie l’élément auquel le QR est associé.

Cette séparation est importante car :

- une référence peut être reçue plusieurs fois ;
- un QR doit rester stable ;
- le système peut avoir besoin de suivre un article individuellement.

Le format de référence reste un **choix de conception à définir**.

---

# 32. QR CODE

Principe :

```text
QR
 ↓
Identifiant stable
 ↓
Fiche article dans l’application
 ↓
Informations visibles selon le rôle
```

Ne pas encoder toutes les données métier dans le QR.

Avantages :

- modification des données sans changer le QR ;
- contrôle des droits ;
- traçabilité centralisée ;
- possibilité d’ajouter des informations plus tard.

Le QR doit être associé à un **article** conformément à la décision métier reçue.

---

# 33. RETOURS

Flux technique proposé :

```text
Produit sorti
   ↓
Retour
   ↓
Contrôle
   ├── utilisable → réintégration
   │
   └── endommagé / hors service
           ↓
       traitement adapté
```

Le statut « retour reçu mais non contrôlé » doit être distinct du stock disponible.

---

# 34. INVENTAIRE ET ÉCARTS

L’inventaire doit permettre :

```text
Stock théorique
        +
Inventaire physique
        ↓
Comparaison
        ↓
Écart
```

Exemple :

```text
Théorique : 50
Physique  : 47
Écart     : -3
```

Ne jamais créer artificiellement une sortie pour équilibrer les chiffres.

Workflow cible :

```text
DÉTECTÉ
   ↓
EN INVESTIGATION
   ↓
TRAITEMENT / JUSTIFICATION
   ↓
VALIDATION AUDIT
   ↓
CLÔTURÉ
```

Le workflow exact des permissions sera implémenté après traduction des responsabilités métier.

---

# 35. FIN D’UTILISATION

Le cycle de vie doit permettre de conserver un produit dans l’historique tout en pouvant le désactiver ultérieurement.

Exemples de situations :

- perdu après investigation ;
- définitivement hors service ;
- désactivé après traitement.

La mise hors service doit intégrer :

- constat par technicien ;
- validation DSI.

Le système doit conserver l’historique même après désactivation.

---

# 36. NOTIFICATIONS

Le workflow prévoit des notifications :

- après saisie/autorisation DSID → utilisateur chargé de valider ;
- après validation → CAME + DSID ;
- après rejet → DSID.

Le canal peut être :

- tableau de bord ;
- email.

Pour le MVP, le tableau de bord est prioritaire.

L’email peut être implémenté si le temps et l’environnement le permettent.

---

# 37. ARCHITECTURE TECHNIQUE CIBLE

## Frontend

**React**

Responsabilités :

- interface utilisateur ;
- formulaires ;
- tableaux ;
- recherche/filtres ;
- dashboard ;
- scan/lecture QR ;
- affichage des statuts ;
- notifications visuelles.

## Backend

**Python + Django + Django REST Framework**

Responsabilités :

- logique métier ;
- authentification ;
- permissions ;
- validation ;
- calcul du stock ;
- API REST ;
- historique ;
- audit ;
- workflow BS ;
- gestion des corrections.

## Base de données

**PostgreSQL**

Responsabilités :

- persistance ;
- contraintes d’intégrité ;
- relations ;
- transactions ;
- recherche ;
- historique.

## FastAPI

FastAPI reste **optionnel**.

Il ne doit être introduit que si un besoin réel le justifie, par exemple un microservice indépendant pour une fonctionnalité spécifique.

Il ne faut pas ajouter FastAPI simplement parce qu’il est disponible.

---

# 38. STRUCTURE LOGIQUE

```text
                    PAOSITRA SMART ASSET
                           │
          ┌────────────────┴────────────────┐
          │                                 │
       FRONTEND                          BACKEND
       React                     Django + Django REST
          │                                 │
          └────────────── API ──────────────┘
                           │
                       PostgreSQL
                           │
                    Données métier
```

---

# 39. PRINCIPES DE QUALITÉ

Le système doit respecter :

- séparation frontend/backend ;
- validation côté backend ;
- contraintes PostgreSQL ;
- permissions par rôle ;
- transactions pour les opérations sensibles ;
- journalisation ;
- aucune suppression destructive des données importantes ;
- gestion propre des erreurs ;
- données de test clairement identifiées ;
- secrets hors du code ;
- sauvegardes ;
- Git/GitHub ;
- documentation.

---

# 40. DONNÉES DE TEST

Pendant le développement :

> **Les données utilisées pour les démonstrations doivent être explicitement identifiées comme données de test.**

Il ne faut jamais présenter des données inventées comme des données réelles de Paositra.

Les vraies données pourront être intégrées lorsque Paositra les fournira selon les conditions d'utilisation autorisées.

---

# 41. CE QUI EST HORS PÉRIMÈTRE

Pour protéger le délai de 3 mois, le projet ne doit pas dériver vers :

- gestion administrative complète des demandes ;
- compatibilité produit ↔ équipement ;
- fonctionnalités sans besoin métier ;
- application mobile native ;
- IA ajoutée artificiellement ;
- architecture microservices inutile ;
- automatisations non nécessaires ;
- fonctionnalités avancées avant stabilisation du cœur.

---

# 42. MVP PRIORITAIRE

Le MVP doit absolument permettre :

1. connexion ;
2. rôles et permissions ;
3. gestion des produits ;
4. catégories/types configurables ;
5. références ;
6. entrées ;
7. stock ;
8. Bon de Sortie ;
9. autorisation DSID ;
10. validation ;
11. sortie effective CAME ;
12. directions ;
13. transferts/mouvements ;
14. retours ;
15. inventaire ;
16. écarts ;
17. corrections traçables ;
18. historique ;
19. QR ;
20. consultation adaptée aux rôles.

---

# 43. FONCTIONNALITÉS « PLUS »

Après stabilisation du cœur :

- dashboard avancé ;
- indicateurs ;
- alertes ;
- notifications email ;
- statistiques ;
- export ;
- recherche avancée ;
- amélioration UX ;
- rapports.

---

# 44. IA : POSITIONNEMENT

L’IA n’est pas le cœur du système.

La priorité est :

> **données fiables → processus fiable → historique fiable → analyse fiable**

Si suffisamment de données historiques sont disponibles, une fonctionnalité d’analyse ou de prédiction pourra être étudiée.

Mais :

> **Le projet doit rester complètement démontrable sans IA.**

L’IA ne doit donc jamais être utilisée pour masquer un problème de conception ou de qualité des données.

---

# PARTIE C — PLAN DE TRAVAIL SUR 3 MOIS

# 45. VUE D’ENSEMBLE

Objectif au bout de 3 mois :

> disposer d’une application fonctionnelle, testée, documentée et présentable devant un encadreur/jury, couvrant le cœur du processus réel validé avec Paositra.

---

# MOIS 1 — COMPRENDRE, CONCEVOIR, CONSTRUIRE LES FONDATIONS

## Semaine 1 — Cadrage final

Objectifs :

- stabiliser PROJECT_CONCEPT ;
- établir le glossaire ;
- formaliser les acteurs ;
- formaliser le workflow BS ;
- formaliser les règles de stock ;
- formaliser retours, inventaire, écarts et fin d’utilisation ;
- identifier les derniers choix techniques.

Livrables :

- PROJECT_CONCEPT ;
- règles métier ;
- workflow ;
- glossaire.

---

## Semaine 2 — Modélisation

Construire :

- MCD MERISE dans Looping ;
- cardinalités ;
- entités ;
- associations ;
- contraintes métier ;
- premiers cas d’utilisation ;
- architecture générale.

Livrables :

- MCD validé ;
- diagrammes nécessaires ;
- schéma fonctionnel.

---

## Semaine 3 — Base de données + backend

Mettre en place :

- projet Django ;
- PostgreSQL ;
- modèles ;
- migrations ;
- contraintes ;
- données de test ;
- administration de base.

Objectif :

> la base doit correctement représenter le métier avant de construire beaucoup d’interface.

---

## Semaine 4 — API + authentification

Construire :

- comptes ;
- rôles ;
- connexion ;
- permissions ;
- API REST ;
- premiers endpoints ;
- gestion des erreurs ;
- traçabilité du compte connecté.

À la fin du mois 1 :

> **la fondation technique fonctionne.**

---

# MOIS 2 — CONSTRUIRE LE CŒUR MÉTIER

## Semaine 5 — Produits et stock

Construire :

- catégories ;
- types ;
- produits ;
- références ;
- unités ;
- fournisseurs/origines ;
- entrées ;
- calcul du stock.

Tests :

- entrée simple ;
- entrée répétée ;
- cumul ;
- stock insuffisant.

---

## Semaine 6 — Bon de Sortie

Construire :

- BS ;
- lignes de BS ;
- quantité demandée ;
- autorisation DSID ;
- quantité autorisée ;
- refus ;
- deuxième validation ;
- statuts.

Tester le workflow complet.

---

## Semaine 7 — Sortie effective et traçabilité

Construire :

- interface CAME ;
- quantité réellement délivrée ;
- sortie effective ;
- direction destinataire ;
- historique ;
- mouvements/transferts.

Tester :

```text
BS
→ autorisation
→ validation
→ CAME
→ sortie
→ destination
```

---

## Semaine 8 — Retours + inventaire

Construire :

- retours ;
- contrôle de retour ;
- réintégration ;
- inventaire ;
- calcul des écarts ;
- alertes d’écart ;
- suivi d’investigation.

À la fin du mois 2 :

> **le cœur opérationnel doit fonctionner de bout en bout.**

---

# MOIS 3 — FINALISER, SÉCURISER, VALIDER ET PRÉSENTER

## Semaine 9 — Corrections + fin d’utilisation

Construire :

- système de correction non destructive ;
- motif ;
- auteur ;
- historique ;
- perte ;
- hors service ;
- validation DSI ;
- désactivation.

---

## Semaine 10 — QR + dashboard

Construire :

- génération QR ;
- association article/QR ;
- scan ;
- fiche article ;
- dashboard ;
- indicateurs ;
- alertes utiles.

Le dashboard ne doit afficher que des indicateurs ayant une utilité métier.

---

## Semaine 11 — Tests et sécurité

Tester :

### Tests fonctionnels

- entrée ;
- stock ;
- BS ;
- autorisation ;
- validation ;
- sortie ;
- transfert ;
- retour ;
- inventaire ;
- écart ;
- correction ;
- fin d’utilisation.

### Tests de permissions

Vérifier qu’un rôle ne peut pas effectuer une opération interdite.

### Tests d’intégrité

Exemples :

- sortie > stock ;
- quantité négative ;
- BS incohérent ;
- correction destructive ;
- retour compté trop tôt.

### Tests techniques

- API ;
- base de données ;
- erreurs ;
- authentification ;
- frontend.

---

## Semaine 12 — Documentation + soutenance

Finaliser :

- documentation technique ;
- documentation utilisateur ;
- architecture ;
- MCD ;
- UML ;
- captures d’écran ;
- scénarios de démonstration ;
- tests ;
- limites ;
- perspectives ;
- présentation orale.

Préparer une démonstration complète :

```text
Connexion
   ↓
Entrée produit
   ↓
Stock
   ↓
BS
   ↓
Autorisation DSID
   ↓
Validation
   ↓
Sortie CAME
   ↓
Direction
   ↓
Transfert
   ↓
Retour
   ↓
Inventaire
   ↓
Écart
   ↓
Correction / traitement
   ↓
Historique
   ↓
QR
   ↓
Dashboard
```

---

# 46. ORDRE DE PRIORITÉ ABSOLU

Si le temps devient insuffisant, l’ordre est :

## PRIORITÉ 1 — INDISPENSABLE

- base de données ;
- authentification ;
- rôles ;
- produits ;
- entrées ;
- stock ;
- BS ;
- autorisation ;
- validation ;
- sortie ;
- historique.

## PRIORITÉ 2 — TRÈS IMPORTANT

- directions ;
- transferts ;
- retours ;
- inventaire ;
- écarts ;
- corrections ;
- fin d’utilisation.

## PRIORITÉ 3 — VALORISATION

- QR ;
- dashboard ;
- alertes ;
- notifications ;
- exports.

## PRIORITÉ 4 — BONUS

- IA ;
- prédiction ;
- fonctionnalités avancées.

**On ne sacrifie jamais le cœur métier pour terminer un bonus.**

---

# 47. CRITÈRE DE RÉUSSITE DU PROJET

Le projet sera considéré comme réussi si un utilisateur peut démontrer un scénario réaliste complet :

> « Un produit arrive au CAME. Il est enregistré. Il entre dans le stock. Un BS est saisi. La DSID autorise une quantité. Une deuxième instance valide. Le CAME enregistre la quantité réellement sortie. Le produit est attribué à une direction. Il peut être transféré. Il peut éventuellement revenir. Un inventaire peut révéler un écart. L’écart est suivi sans inventer de mouvement. Une correction est traçable. Enfin, le produit peut arriver en fin d’utilisation tout en conservant son historique. »

Si ce scénario fonctionne correctement, le projet possède déjà une forte valeur métier et académique.

---

# 48. RÈGLES DE TRAVAIL DE L’ÉQUIPE IA

Les assistants IA utilisés pour le projet doivent respecter :

### 1. Ne jamais inventer une règle Paositra.

Si l’information n’est pas connue :

**À CONFIRMER / NC**

### 2. Ne jamais modifier silencieusement le périmètre.

Toute modification importante doit être présentée comme :

**PROPOSITION — À VALIDER**

### 3. Ne pas coder avant de comprendre.

Pour chaque fonctionnalité :

```text
Pourquoi ?
↓
Quelle règle métier ?
↓
Quelles données ?
↓
Quelle logique ?
↓
Quelle architecture ?
↓
Code
↓
Test
```

### 4. Ne pas produire du code que l’étudiante ne peut pas expliquer.

Le projet doit rester défendable par sa développeuse.

### 5. Utiliser l’IA comme assistance, pas comme source de vérité métier.

La source de vérité est :

1. fonctionnement réel validé par Paositra ;
2. décisions du projet ;
3. documentation technique officielle ;
4. raisonnement de conception.

---

# 49. RÉPARTITION DU TRAVAIL ENTRE LES OUTILS IA

## ChatGPT — Chef de projet / architecte / mentor

Responsabilités :

- cohérence globale ;
- architecture ;
- métier ;
- MCD ;
- planification ;
- décisions ;
- pédagogie ;
- tests ;
- préparation soutenance.

## Claude — Auditeur métier

Responsabilités :

- challenger les règles ;
- détecter les incohérences ;
- chercher les cas limites ;
- vérifier le réalisme.

## Gemini — Implémentation / debugging

Responsabilités :

- aide à l’implémentation ;
- génération ciblée ;
- debugging ;
- explication des erreurs.

## Cursor — Intégration / tests

Responsabilités :

- intégration du code ;
- cohérence des fichiers ;
- exécution ;
- tests ;
- corrections techniques.

Les décisions importantes restent sous contrôle du projet.

---

# 50. ÉTAT DU PROJET APRÈS LE CADRAGE

## DÉFINITIVEMENT ÉTABLI

- nom et orientation du projet ;
- CAME = Centre d’Approvisionnement en Matériels et Equipements ;
- stock central au CAME ;
- DSID ;
- rôles principaux ;
- workflow réel du BS ;
- distinction demandé / autorisé / réellement sorti ;
- validation par deuxième instance ;
- sortie effective par CAME ;
- catégories/types configurables ;
- gestion pièce/lot ;
- retours avec contrôle avant réintégration ;
- implication de l’Audit dans les écarts ;
- fin d’utilisation et hors service ;
- conservation de l’historique ;
- désactivation ultérieure ;
- QR par article ;
- authentification : **compte + nom associé + rôle** ;
- traçabilité automatique du compte connecté ;
- PostgreSQL ;
- Django + DRF ;
- React ;
- projet réalisable par étapes sur environ 3 mois ;
- IA non obligatoire pour le fonctionnement du cœur.

## CHOIX TECHNIQUES À FINALISER PENDANT LA CONCEPTION

Ce ne sont pas des trous dans le métier : ce sont des décisions de conception à prendre avant ou pendant le MCD :

- format exact de référence interne ;
- structure exacte Produit / Référence / Article / Lot ;
- représentation technique du QR ;
- détail des statuts ;
- structure précise des notifications ;
- structure exacte du journal d’audit ;
- détail des permissions par rôle ;
- structure finale des entités du MCD.

Ces choix doivent rester cohérents avec les décisions métier déjà établies.

---

# 51. PHILOSOPHIE FINALE

PAOSITRA SMART ASSET ne doit pas être présenté comme :

> « un simple logiciel de stock ».

Il s’agit plutôt d’un :

> **système de gestion, d’inventaire et de traçabilité des produits, permettant de conserver une mémoire fiable des entrées, validations, sorties, destinations, mouvements, retours, inventaires et fins d’utilisation.**

La valeur du système vient de la combinaison :

# DONNÉES FIABLES
→
# STOCK MAÎTRISÉ
→
# TRAÇABILITÉ
→
# HISTORIQUE
→
# CONTRÔLE
→
# AIDE À LA DÉCISION

Le projet doit rester **réaliste, professionnel, défendable académiquement et terminable en trois mois**.

---

# FIN DU PROJECT_CONCEPT

**Document de référence — PAOSITRA SMART ASSET**
