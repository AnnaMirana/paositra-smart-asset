# PAOSITRA SMART ASSET — Journal de décisions & Guide de compréhension

Ce document sert deux objectifs à la fois : garder la trace de chaque décision technique prise (et pourquoi), et servir de support pour comprendre et défendre le projet à l'oral. Il est mis à jour après chaque bloc de développement important, pas après chaque ligne de code.

Statuts utilisés partout dans ce document :
- **VALIDÉ** = décision prise et appliquée.
- **À CONFIRMER** = en attente d'une information de Paositra.
- **PROPOSITION** = choix technique par défaut, à réexaminer si besoin.

---

# 1. Objectif du projet

**PAOSITRA SMART ASSET** est un système de gestion, d'inventaire et de traçabilité des produits/matériels de Paositra. Il doit permettre de suivre un produit depuis son entrée au CAME jusqu'à la fin de son utilisation : réception, stockage, demande de sortie, autorisation, validation, sortie physique vers une direction, transferts éventuels, retours, inventaires, écarts, corrections.

**Ce que le système ne fait pas** (hors périmètre) : il ne gère pas l'acceptation administrative des demandes (la décision politique/budgétaire d'accorder un produit à une direction se prend en dehors du système), ni la compatibilité produit/équipement, ni la gestion complète de la réparation (étudiée plus tard si le temps le permet).

---

# 2. Contexte métier Paositra

- **CAME** = Centre d'Approvisionnement en Matériels et Équipements. C'est là que le stock physique est centralisé.
- **DSID** = le service qui supervise le processus de stock, l'inventaire et les mouvements, et qui autorise les sorties.
- Les fournisseurs approvisionnent le CAME ; les produits arrivent, sont vérifiés/inventoriés, puis enregistrés en stock.
- Les directions demandent des produits via un **Bon de Sortie (BS)**.
- Une sortie peut contenir plusieurs types de produits ; chaque ligne du BS génère son propre suivi.
- Une sortie supérieure au stock disponible doit être bloquée.
- Un produit peut être transféré plusieurs fois entre directions, et peut revenir vers le CAME (retour).
- Le suivi va jusqu'à la fin d'utilisation du produit (hors service, perte, etc.).

---

# 3. Workflow métier complet — le circuit du Bon de Sortie

C'est le processus réel observé sur le terrain, tel que décrit par l'encadreur Paositra :

1. Une direction émet un **Bon de Sortie (BS)** avec la quantité demandée par article.
2. Le **DSID** consulte le stock disponible.
3. Le DSID **autorise ou refuse**, avec une quantité autorisée par article (peut différer de la quantité demandée).
4. Une **2ᵉ instance** valide ou rejette le BS.
5. Si validé, le BS arrive au **CAME**.
6. Le CAME prépare et fournit physiquement les articles.
7. Le CAME enregistre la **quantité réellement livrée** (peut différer de la quantité autorisée, ex. rupture de stock physique imprévue).
8. Les articles sont transmis à la direction avec un **Soit Transmis (ST)**.
9. Le demandeur signe le ST.
10. Le ST signé revient au DSID (document, pour l'instant hors système, traité comme simple champ texte).

**Point de vocabulaire important à distinguer** :
- **Demande** (`LigneBSortie.quantite_demandee`) = ce que la direction a demandé au départ.
- **Autorisation/Validation/Livraison** (`LigneSortie.quantite_autorisee` / `quantite_livree`) = ce qui a été effectivement décidé puis exécuté.

Ces deux notions ne sont jamais fusionnées dans le modèle — voir section 15.

---

# 4. Stack technique

| Composant | Choix | Pourquoi |
|---|---|---|
| Backend | Python + Django + Django REST Framework | Framework mature, rapide à mettre en œuvre, ORM intégré, adapté à un projet de gestion avec authentification et permissions. |
| Frontend | React | Séparation claire frontend/backend, interface dynamique, communication via API REST. |
| Base de données | PostgreSQL | Contraintes d'intégrité strictes, gestion robuste de la concurrence, adapté à un vrai système de gestion (contrairement à SQLite, gardé pour des projets plus petits ou du prototypage). |
| ORM | Django ORM | Fourni nativement avec Django, évite d'écrire du SQL à la main pour les opérations courantes. |
| Communication | API REST (JSON) | Standard, découplé, permet au frontend d'évoluer indépendamment du backend. |
| Versioning | Git / GitHub | Suivi de l'historique du code, travail en équipe (chef de projet, développeuse, autres IA). |

**Principe d'architecture** :
```
React (frontend) → requêtes HTTP → API Django REST Framework → Django ORM → PostgreSQL
```

---

# 5. Architecture générale du projet

```
PAOSITRA_SMART_ASSET/
├── backend/          → projet Django (API, modèles, logique métier)
│   ├── venv/         → environnement Python isolé (jamais sur Git)
│   ├── config/       → configuration centrale Django (settings, urls)
│   ├── inventaire/   → application métier (tous les modèles du MCD)
│   ├── manage.py
│   ├── .env          → identifiants sensibles (jamais sur Git)
│   └── .gitignore
├── frontend/         → application React (pas encore commencée à ce stade)
└── docs/             → documentation du projet, dont ce fichier
```

---

# 6. Installation de l'environnement (commandes réellement exécutées)

1. Vérification de l'absence de PostgreSQL (`psql --version` → erreur "non reconnu").
2. Téléchargement et installation de PostgreSQL 16 (installateur officiel EDB pour Windows).
3. Ajout manuel de `C:\Program Files\PostgreSQL\16\bin` au PATH Windows (l'installateur ne l'avait pas fait automatiquement).
4. `cd backend`
5. `python -m venv venv` → création de l'environnement virtuel Python, isolé du reste de la machine.
6. `venv\Scripts\activate` → activation (repérable au préfixe `(venv)` dans le terminal).
7. `pip install django psycopg2-binary python-dotenv` → framework, connecteur PostgreSQL, gestion du fichier `.env`.
8. `django-admin startproject config .` → création du projet Django (le `.` évite un sous-dossier en trop).
9. `python manage.py startapp inventaire` → création de l'application métier.
10. `pip install djangorestframework` → préparation de la future API.

**Pourquoi un environnement virtuel (`venv`) ?** Pour isoler les paquets Python de ce projet du reste de la machine — deux projets différents peuvent ainsi utiliser des versions différentes de Django sans conflit.

---

# 7. PostgreSQL — configuration

```sql
CREATE DATABASE paositra_db;
CREATE USER paositra_user WITH PASSWORD '...';
GRANT ALL PRIVILEGES ON DATABASE paositra_db TO paositra_user;
```

**Pourquoi un utilisateur dédié (`paositra_user`) plutôt que le superadmin `postgres` ?**
Django n'a besoin que des droits sur sa propre base, pas de droits d'administration sur tout le serveur — principe de moindre privilège.

### Incident 1 — `psql` non reconnu
L'installateur Windows n'ajoute pas toujours PostgreSQL au PATH. Résolu en l'ajoutant manuellement dans les variables d'environnement système, puis en rouvrant le terminal (un terminal déjà ouvert ne voit pas un changement de PATH fait pendant qu'il tourne).

### Incident 2 — "droit refusé pour le schéma public"
Depuis PostgreSQL 15, `GRANT ALL PRIVILEGES ON DATABASE` ne donne plus automatiquement le droit de créer des tables dans le schéma `public`. Résolu par :
```sql
\c paositra_db
GRANT ALL ON SCHEMA public TO paositra_user;
ALTER DATABASE paositra_db OWNER TO paositra_user;
```

**Question de jury — "Pourquoi PostgreSQL et pas MySQL ?"**
Réponse réelle du projet : ce n'est pas un choix comparatif fait par nous — c'était une contrainte technique validée dès le cadrage initial avec l'encadreur et le chef de projet, pour la robustesse des contraintes d'intégrité sur un système de gestion.

---

# 8. Structure Django

- **Projet** (`config/`) = la configuration globale (réglages, routage général). Un seul par site.
- **Application** (`inventaire/`) = un module regroupant une logique métier cohérente. On aurait pu en faire plusieurs (une pour les entrées, une pour les sorties...) mais une seule application suffit pour la taille de ce projet — éviter la sur-ingénierie.

`INSTALLED_APPS` dans `config/settings.py` déclare les applications actives : `inventaire`, `rest_framework`, plus les applications Django internes par défaut (`admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`).

---

# 9. Authentification / Utilisateur

**Décision** : modèle `Utilisateur` personnalisé, héritant de `AbstractUser` (fourni par Django), plutôt que le `User` par défaut + une table `Profil` séparée.

**Pourquoi ce choix plutôt que l'autre ?**
Le MCD prévoit une seule entité `UTILISATEUR`. Garder le `User` standard + un `Profil` séparé aurait créé deux tables pour un seul concept métier, plus lourd à interroger (jointure systématique) et plus difficile à justifier ("pourquoi deux tables Utilisateur ?").

`AbstractUser` fournit automatiquement : gestion sécurisée des mots de passe (hachage, jamais stocké en clair), `username`, `first_name`, `last_name`, `email`, compatibilité native avec l'authentification Django et l'interface d'admin.

```python
class Utilisateur(AbstractUser):
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    actif = models.BooleanField(default=True)
```

**Rôles définis (PROPOSITION, reprise des échanges avec l'encadreur)** : `administrateur`, `agent_dsid`, `agent_validation`, `agent_came`, `demandeur`, `agent_direction`, `auditeur`.

### Incident — réinitialisation de la base
Django exige que `AUTH_USER_MODEL` soit défini **avant** la toute première migration, pas après. Comme `migrate` avait déjà été lancé une première fois avec le modèle utilisateur par défaut (pour tester la connexion), il a fallu réinitialiser la base (`DROP DATABASE` puis `CREATE DATABASE`) avant de créer le modèle personnalisé. Aucune donnée réelle n'a été perdue (seulement des tables vides).

**Règle de suppression** : un utilisateur n'est jamais supprimé, seulement désactivé (`actif = False`) — cohérent avec la règle générale "jamais de suppression". C'est pour ça que `on_delete=PROTECT` est utilisé sur toutes les relations pointant vers `Utilisateur`.

---

# 10. MCD complet (état actuel)

## Entités et attributs principaux

| Entité | Attributs clés |
|---|---|
| UTILISATEUR | identifiant, nom, mot_de_passe (haché), role, actif |
| CATEGORIE | nom_categorie |
| TYPE_ARTICLE | nom_type_article, quantite_stock, gestion_individuelle |
| ARTICLE | ref_article, qr_code (facultatif), num_serie, marque, caracteristique |
| FOURNISSEUR | nom_fournisseur, informations |
| ENTREE | date_entree, document, ref_entree, origine |
| LIGNE_ENTREE | quantite |
| DIRECTION | nom_direction, service |
| BON_SORTIE | reference_bs, document, date_bs, statut |
| LIGNE_BSORTIE | quantite_demandee |
| SORTIE | date_sortie, quantite, ref_sortie |
| LIGNE_SORTIE | quantite_demandee, quantite_autorisee, quantite_livree |
| MOUVEMENT | date_mouvement, type_mouvement, quantite (conditionnelle) |
| INTERVIENT (association) | role_intervention, date_intervention |

## Relations et cardinalités (état actuel, après corrections)

```
CATEGORIE        (1,n) ↔ (1,1)  TYPE_ARTICLE
TYPE_ARTICLE      (0,n) ↔ (1,1)  ARTICLE
FOURNISSEUR       (0,n) ↔ (0,1)  ENTREE
ENTREE            (1,n) ↔ (1,1)  LIGNE_ENTREE
TYPE_ARTICLE      (0,n) ↔ (1,1)  LIGNE_ENTREE
LIGNE_ENTREE      (0,n) ↔ (1,1)  ARTICLE
UTILISATEUR       (0,n) ↔ (1,1)  ENTREE
TYPE_ARTICLE      (0,n) ↔ (1,1)  LIGNE_BSORTIE
LIGNE_BSORTIE     (1,1) ↔ (1,n)  BON_SORTIE
BON_SORTIE        (1,1) ↔ (0,n)  DIRECTION
BON_SORTIE        (1,n) ↔ (0,n)  UTILISATEUR   — via INTERVIENT
TYPE_ARTICLE      (0,n) ↔ (1,1)  LIGNE_SORTIE
LIGNE_SORTIE      (1,1) ↔ (1,n)  SORTIE
SORTIE            (1,1) ↔ (0,1)  BON_SORTIE
SORTIE            (0,n) ↔ (0,n)  ARTICLE        — corrigé (était 1,n)
ARTICLE           (0,n) ↔ (0,1)  MOUVEMENT       — corrigé (était 1,1)
TYPE_ARTICLE      (0,n) ↔ (0,1)  MOUVEMENT       — nouveau
UTILISATEUR       (0,n) ↔ (1,1)  MOUVEMENT
MOUVEMENT         (0,n) ↔ (0,1)  DIRECTION       — optionnel (une entrée au CAME n'a pas de direction)
UTILISATEUR       (0,n) ↔ (0,n)  DIRECTION
```

**Relations volontairement absentes** (pour éviter les chemins redondants) : `TYPE_ARTICLE ↔ FOURNISSEUR`, `TYPE_ARTICLE ↔ ENTREE`, `ARTICLE ↔ FOURNISSEUR`, `ARTICLE ↔ DIRECTION`, `LIGNE_BSORTIE ↔ LIGNE_SORTIE` (ce dernier cas est un compromis assumé, voir section 30).

---

# 11. Correspondance générale MCD → Django

| Notion MCD | Traduction Django | Explication |
|---|---|---|
| Entité | `class MonModele(models.Model)` | Chaque entité devient une classe Python. |
| Identifiant (id_xxx) | rien à écrire | Django crée automatiquement une clé primaire `id` auto-incrémentée. |
| Attribut texte court | `CharField(max_length=...)` | Longueur maximale obligatoire en PostgreSQL. |
| Attribut texte long | `TextField()` | Pas de limite de longueur. |
| Attribut date | `DateField()` / `DateTimeField()` | Avec ou sans heure. |
| Attribut nombre positif | `PositiveIntegerField()` | Interdit les valeurs négatives au niveau base de données (ex. un stock ne peut pas être négatif). |
| Attribut oui/non | `BooleanField(default=...)` | |
| Cardinalité `(1,1)` côté X vers Y | `ForeignKey` obligatoire sur X (pas de `null=True`) | X doit toujours être lié à un Y. |
| Cardinalité `(0,1)` côté X vers Y | `ForeignKey` avec `null=True, blank=True` sur X | X peut exister sans être lié à un Y. |
| Association 1-N | `ForeignKey` posée sur l'entité côté "N" (le "plusieurs") | Toujours le côté N qui porte la référence vers le côté 1, jamais l'inverse. |
| Association N-N | `ManyToManyField` | Chaque côté peut être lié à plusieurs occurrences de l'autre. |
| Association N-N avec attributs propres (ex. INTERVIENT) | `ManyToManyField(through='NomAssociation')` + une classe séparée pour l'association | Une simple M2M ne peut pas porter d'attributs (comme `role_intervention`), il faut une table intermédiaire explicite. |
| Association 1-1 | `OneToOneField` | Chaque occurrence de X correspond à au plus une occurrence de Y, et inversement. |
| Suppression protégée (jamais de perte d'historique) | `on_delete=models.PROTECT` | Django refuse la suppression tant que des objets liés existent. |
| Suppression en cascade (l'enfant n'a pas de sens seul) | `on_delete=models.CASCADE` | Supprimer le parent supprime aussi l'enfant. |
| Liste de valeurs fixes | `choices=[...]` sur un `CharField` | Validation au niveau application, pas une contrainte stricte en base (une colonne `VARCHAR` classique). |
| Valeur générée automatiquement (ex. date de création) | `auto_now_add=True` | Rempli une seule fois, à la création, non modifiable ensuite. |

---

# 12. Fiche de chaque modèle Django

## 12.1 Categorie
```python
class Categorie(models.Model):
    nom_categorie = models.CharField(max_length=100)
```
**Rôle** : classe les types d'articles (ex. "Informatique", "Consommables").

## 12.2 Fournisseur
```python
class Fournisseur(models.Model):
    nom_fournisseur = models.CharField(max_length=150)
    informations = models.TextField(blank=True, null=True)
```
**Rôle** : représente l'origine fournisseur d'une entrée, quand elle existe (voir section 30 sur le cas des dons).

## 12.3 Direction
```python
class Direction(models.Model):
    nom_direction = models.CharField(max_length=150)
    service = models.CharField(max_length=150, blank=True, null=True)
```
**Rôle** : représente la direction/service destinataire d'un Bon de Sortie.

## 12.4 Utilisateur
Voir section 9 pour le détail complet.
**Rôle** : représente une personne qui utilise le système, avec un rôle métier et un statut actif/inactif.

## 12.5 TypeArticle
```python
class TypeArticle(models.Model):
    nom_type_article = models.CharField(max_length=150)
    quantite_stock = models.PositiveIntegerField(default=0)
    gestion_individuelle = models.BooleanField(default=False)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='types_article')
```
| Champ | Pourquoi |
|---|---|
| `nom_type_article` | nom générique du produit (ex. "Ordinateur portable") |
| `quantite_stock` | stock disponible pour ce type — recalculé automatiquement, jamais saisi à la main (logique pas encore codée) |
| `gestion_individuelle` | décide si ce type génère des `Article` un par un, ou juste une quantité globale |
| `categorie` | rattache le type à sa catégorie |

## 12.6 Entree
```python
class Entree(models.Model):
    date_entree = models.DateField()
    document = models.CharField(max_length=255, blank=True, null=True)
    ref_entree = models.CharField(max_length=100, unique=True)
    origine = models.CharField(max_length=20, choices=ORIGINE_CHOICES)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, null=True, blank=True, related_name='entrees')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='entrees_enregistrees')
```
**Rôle** : représente une opération d'entrée de produits au CAME (réception fournisseur ou don).

## 12.7 LigneEntree
```python
class LigneEntree(models.Model):
    quantite = models.PositiveIntegerField()
    entree = models.ForeignKey(Entree, on_delete=models.CASCADE, related_name='lignes')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_entree')
```
**Rôle** : détaille les types et quantités reçus dans une entrée (une entrée peut contenir plusieurs types de produits).

## 12.8 Article
```python
class Article(models.Model):
    qr_code = models.CharField(max_length=255, unique=True, blank=True, null=True)
    num_serie = models.CharField(max_length=150, blank=True, null=True)
    ref_article = models.CharField(max_length=150)
    marque = models.CharField(max_length=150, blank=True, null=True)
    caracteristique = models.TextField(blank=True, null=True)
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='articles')
    ligne_entree = models.ForeignKey(LigneEntree, on_delete=models.PROTECT, related_name='articles')
```
**Rôle** : représente un exemplaire physique précis (uniquement pour les types en `gestion_individuelle=True`).

## 12.9 BonSortie
```python
class BonSortie(models.Model):
    reference_bs = models.CharField(max_length=100, unique=True)
    document = models.CharField(max_length=255, blank=True, null=True)
    date_bs = models.DateField()
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='brouillon')
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='bons_sortie')
    utilisateurs = models.ManyToManyField(Utilisateur, through='Intervient', related_name='bons_sortie')
```
**Rôle** : représente la demande officielle de sortie émise par une direction. Voir section 10 pour la liste `statut`.

## 12.10 LigneBSortie
```python
class LigneBSortie(models.Model):
    quantite_demandee = models.PositiveIntegerField()
    bon_sortie = models.ForeignKey(BonSortie, on_delete=models.CASCADE, related_name='lignes')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_bsortie')
```
**Rôle** : détaille ce qui est demandé dans un Bon de Sortie (un type de produit + une quantité).

## 12.11 Intervient
```python
class Intervient(models.Model):
    bon_sortie = models.ForeignKey(BonSortie, on_delete=models.CASCADE, related_name='interventions')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='interventions')
    role_intervention = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_intervention = models.DateTimeField(auto_now_add=True)
```
**Rôle** : trace qui a autorisé et qui a validé un Bon de Sortie, avec la date de chaque action. Une seule association (pas deux) parce qu'une association MERISE peut porter ses propres attributs.

## 12.12 Sortie
```python
class Sortie(models.Model):
    date_sortie = models.DateField()
    quantite = models.PositiveIntegerField()
    ref_sortie = models.CharField(max_length=100, unique=True)
    bon_sortie = models.OneToOneField(BonSortie, on_delete=models.PROTECT, related_name='sortie')
    articles = models.ManyToManyField(Article, related_name='sorties')
```
**Rôle** : représente la livraison réellement effectuée (au maximum une par Bon de Sortie). Peut être liée à zéro article physique si la sortie ne contient que des consommables (voir Décision 9, section 30).

## 12.13 LigneSortie
```python
class LigneSortie(models.Model):
    quantite_demandee = models.PositiveIntegerField()
    quantite_autorisee = models.PositiveIntegerField()
    quantite_livree = models.PositiveIntegerField()
    sortie = models.ForeignKey(Sortie, on_delete=models.CASCADE, related_name='lignes')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_sortie')
```
**Rôle** : détaille ce qui a réellement été demandé/autorisé/livré, par type de produit, dans une sortie effective.

## 12.14 Mouvement
```python
class Mouvement(models.Model):
    date_mouvement = models.DateTimeField(auto_now_add=True)
    type_mouvement = models.CharField(max_length=30, choices=TYPE_MOUVEMENT_CHOICES)
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
    quantite = models.PositiveIntegerField(null=True, blank=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='mouvements_enregistres')
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
```
**Rôle** : garde la trace de tout déplacement/changement de statut d'un article ou d'une quantité de type. C'est l'historique du projet — il n'existe pas d'entité "Historique" séparée, tout se retrouve via les `Mouvement` liés.

---

# 13-14. Pourquoi chaque champ / chaque relation existe

Voir le détail intégré dans chaque fiche de la section 12, et le tableau générique de la section 11. Les choix `PROTECT` vs `CASCADE` suivent une règle unique dans tout le projet :

> **`PROTECT`** quand l'objet lié existe indépendamment de la relation et qu'on ne veut jamais perdre d'historique par accident (un utilisateur, un type d'article, un article physique, un fournisseur, une direction).
> **`CASCADE`** uniquement quand l'objet n'a **aucun sens tout seul** et n'existe que comme détail d'un autre (une `LigneEntree` sans son `Entree`, une `LigneBSortie`/`LigneSortie` sans son `BonSortie`/`Sortie`, une `Intervient` sans son `BonSortie`).

---

# 15. Règles métier centrales

- **Jamais de suppression définitive** d'une donnée. Une correction ne supprime pas l'ancienne valeur, elle en ajoute une nouvelle avec auteur/date/motif (logique pas encore codée — voir section 20).
- **Sortie > stock disponible = bloquée** (logique pas encore codée — voir section 18).
- **Demande ≠ Réalisation** : `LigneBSortie` (ce qui est demandé) et `LigneSortie` (ce qui est autorisé/livré) restent deux entités séparées, jamais fusionnées.
- **Double traçabilité** : chaque opération importante (entrée, mouvement, intervention sur un BS) enregistre l'utilisateur connecté qui l'a effectuée.
- **Retour contrôlé** : un retour n'est pas automatiquement remis en stock disponible — il passe par un contrôle avant réintégration ou mise hors service (logique pas encore codée).

---

# 16. Gestion des articles individualisés

Quand `TypeArticle.gestion_individuelle = True` (ex. ordinateurs, imprimantes), chaque unité reçue doit donner lieu à la création d'un `Article` distinct, avec sa propre référence et éventuellement un QR code. C'est ce qui permet de savoir "quel ordinateur précis est sorti" (via la relation `Sortie ↔ Article`) et de suivre son historique complet via ses `Mouvement`.

**Logique de création automatique des articles à l'entrée** : pas encore codée à ce stade (prévue lors du développement de la logique métier des entrées).

---

# 17. Gestion des consommables

Quand `TypeArticle.gestion_individuelle = False` (ex. rubans, ramettes de papier), aucun `Article` n'est créé. Le suivi se fait uniquement par quantité, sur `TypeArticle.quantite_stock` et via des `Mouvement` où `type_article` et `quantite` sont renseignés à la place de `article`.

**Exemple concret** : 10 cartouches d'encre sortent vers une direction →
```
LigneSortie.quantite_livree = 10
        ↓
TypeArticle.quantite_stock diminue de 10 (logique pas encore codée)
        ↓
Mouvement.type_article = Cartouche, Mouvement.quantite = 10
        ↓
historique conservé, sans qu'aucun Article n'existe
```

**Pourquoi ne pas créer un Article pour chaque cartouche ?** Parce que `gestion_individuelle=False` — ça n'apporte aucune valeur de traçabilité individuelle pour ce type de produit, et ça ferait exploser le volume de données pour rien.

---

# 18. Gestion du stock

**Pas encore codée à ce stade.** Ce qui est prévu :
- `TypeArticle.quantite_stock` ne sera **jamais** modifiable directement par un formulaire utilisateur.
- Il sera recalculé automatiquement par le backend lors des entrées, sorties effectives, retours réintégrés, corrections.
- La règle "sortie > stock disponible = bloquée" sera appliquée au niveau du code (Django), pas au niveau de la base de données, qui ne peut pas exprimer une règle aussi dynamique.

---

# 19. Traçabilité

Trois mécanismes distincts, à ne pas confondre :
1. **`Utilisateur` sur `Entree` et `Mouvement`** : qui a enregistré cette opération.
2. **`Intervient` sur `BonSortie`** : qui a autorisé, qui a validé, avec quel rôle et à quelle date.
3. **`Mouvement`** : l'historique complet de la vie d'un article (ou d'une quantité de type), consultable à tout moment.

Il n'existe volontairement aucune entité "Historique" séparée — tout est reconstituable via `Mouvement`.

---

# 20. Gestion des erreurs et corrections

**Principe validé, logique pas encore codée** : jamais de suppression. Si une entrée indique 50 imprimantes et qu'un inventaire en trouve 49, l'ancienne valeur (50) reste enregistrée et marquée erronée, une nouvelle valeur (49) est enregistrée avec auteur/date/motif. `Mouvement.type_mouvement = 'correction'` est prévu pour tracer ce cas, mais la logique applicative n'est pas encore écrite.

---

# 21. Migrations appliquées (état à ce stade)

| # | Contenu |
|---|---|
| `0001_initial` | `Categorie`, `Direction`, `Fournisseur`, `Utilisateur` |
| `0002_typearticle` | `TypeArticle` |
| `0003_entree_ligneentree` | `Entree`, `LigneEntree` |
| `0004_typearticle_gestion_individuelle` | ajout du champ `gestion_individuelle` |
| `0005_utilisateur_directions_article_bonsortie_intervient_and_more` | `Article`, `BonSortie`, `Intervient`, `LigneBSortie`, `Sortie`, `LigneSortie`, `Mouvement` (version corrigée), champ `directions` sur `Utilisateur`, champ `utilisateurs` sur `BonSortie` |

---

# 22. Incidents rencontrés et solutions — récapitulatif

| Incident | Cause | Solution |
|---|---|---|
| `psql` non reconnu | PATH Windows non mis à jour par l'installateur | Ajout manuel du dossier `bin` de PostgreSQL au PATH système |
| "droit refusé pour le schéma public" | Comportement PostgreSQL 15+ : `GRANT ALL PRIVILEGES ON DATABASE` ne suffit plus | `GRANT ALL ON SCHEMA public` + `ALTER DATABASE ... OWNER TO ...` |
| Réinitialisation de la base nécessaire | `AUTH_USER_MODEL` doit être défini avant la première migration | `DROP DATABASE` / `CREATE DATABASE`, sans perte car aucune donnée réelle |
| `Mouvement.article` obligatoire bloquait les consommables | Le MCD n'avait pas anticipé le cas des types non individualisés | `article` et `type_article` rendus optionnels, ajout de `quantite`, règle d'exclusivité via `clean()` |

## Décision 10 — Logique métier centralisée (services.py) + API REST + Admin

STATUT : VALIDÉ (testé dans un environnement de vérification identique, à copier et re-tester dans le vrai projet)

### Décision
Toute la logique métier sensible (création d'articles à l'entrée, calcul du stock, blocage de sortie) est écrite dans un seul fichier `inventaire/services.py`, appelé à la fois par les vues API et, plus tard, potentiellement par l'admin ou une commande d'import. Elle n'est jamais écrite directement dans les vues.

### Pourquoi
Si la règle métier était écrite dans la vue, elle devrait être réécrite (ou copiée-collée, avec le risque d'oubli) à chaque nouvel endroit qui crée une entrée ou une sortie (admin, import en masse, futur script). Centraliser dans `services.py` garantit une seule source de vérité.

### Ce qui a été testé et vérifié (script `test_scenarios.py`)
- Entrée de 5 articles individualisés → 5 `Article` créés, 5 `Mouvement` de type `entree`, `quantite_stock` du type passe à 5 (le stock global du type augmente toujours, individualisé ou non).
- Entrée de 50 consommables → 0 `Article` créé, `quantite_stock` passe à 50, 1 seul `Mouvement` avec `quantite=50`.
- Sortie de 999 consommables alors que le stock est à 50 → **bloquée**, rien n'est écrit en base (transaction annulée).
- Sortie de 5 consommables sur 50 disponibles → acceptée, stock ramené à 45.
- Traçabilité : mouvements consultables aussi bien pour un article individuel que pour un type par quantité.
- Flux complet testé aussi via l'API HTTP réelle (création d'entrée, ajout de ligne, création de bon de sortie) avec `curl`, pas seulement en isolation dans le shell Django.

### API REST — endpoints choisis
`categories`, `types-article` (+ action `stock`), `articles` (lecture seule), `entrees` (+ action `ajouter_ligne`), `bons-sortie`, `sorties` (+ action `effectuer`), `mouvements` (lecture seule). `Article` et `Mouvement` sont volontairement en lecture seule via l'API : ils ne doivent jamais être créés directement, seulement comme conséquence d'une entrée ou d'une sortie passées par `services.py`.

### Simplifications assumées dans ce vertical slice (à ne pas présenter comme terminé)
- Le circuit complet à deux signatures (autorisation DSID puis validation 2ᵉ instance, via `Intervient`) existe dans le modèle mais **n'est pas encore relié à une vue API dédiée** — l'action `effectuer` actuelle exécute directement la sortie à partir d'un `BonSortie` déjà au statut `valide`, sans encore automatiser les étapes intermédiaires.
- La sélection des articles "disponibles" pour une sortie individualisée est naïve (elle exclut simplement les articles déjà liés à une sortie) — elle ne tient pas encore compte des retours réintégrés en stock.
- `ref_article` est générée avec un format temporaire (`REF-ENTREE-TYPE-NUMERO`), pas le format réel Paositra, toujours À CONFIRMER.

### Bug détecté par toi (tests réels) et corrigé
En testant réellement le formulaire Admin (pas seulement l'API), tu as découvert qu'ajouter une ligne d'entrée depuis `Entree → Add → Lignes (inline)` ne créait **aucun** `Article` ni `Mouvement` — contrairement au même scénario passé par l'API (`/ajouter_ligne/`), qui fonctionnait correctement.

**Cause** : l'admin Django, par défaut, sauvegarde une ligne inline directement (`LigneEntree.objects.create(...)`), sans jamais appeler `services.enregistrer_ligne_entree()`. Deux chemins différents (admin et API) pour la même opération, un seul appliquant réellement la règle métier — exactement le genre de désynchronisation que centraliser la logique dans `services.py` était censé éviter, mais qui peut quand même se reproduire si un des points d'entrée ne l'appelle pas.

**Correction** : `EntreeAdmin.save_formset()` est maintenant surchargée pour intercepter la sauvegarde des lignes et appeler `services.enregistrer_ligne_entree()` pour toute nouvelle ligne, au lieu de laisser l'admin sauvegarder directement. Revérifié avec un test simulant exactement le même formulaire que celui rempli à la main (3 ordinateurs → 3 `Article` + 3 `Mouvement` ; 50 cartouches → 0 `Article`, stock à 50).

**Leçon à retenir pour la suite** : chaque nouveau point d'entrée qui touche une entrée ou une sortie (admin, API, futur import) doit explicitement passer par `services.py` — ce n'est pas automatique du simple fait que la fonction existe quelque part dans le projet.

### 2e bug détecté par toi (tests réels) et corrigé
En testant réellement l'action `/sorties/effectuer/` avec un dépassement de stock volontaire, le serveur a planté avec `ValueError: Sortie object can't be deleted because its id attribute is set to None` au lieu de renvoyer proprement une erreur 400.

**Cause** : le code créait la `Sortie` en base **avant** de vérifier le stock, et tentait de la supprimer (`sortie.delete()`) si le blocage se déclenchait. Cette suppression a échoué, laissant une trace corrompue en base — ce qui a aussi cassé le test suivant (le stock ne bougeait plus du tout), car cette trace bloquait toute nouvelle sortie sur le même Bon de Sortie (contrainte d'unicité `Sortie ↔ BonSortie`).

**Correction** : `services.effectuer_sortie` vérifie maintenant le stock **avant** toute écriture ; la `Sortie` n'est créée qu'une fois la vérification passée, le tout dans une seule transaction. Si le stock est insuffisant, rien n'est jamais écrit — pas besoin d'annuler quoi que ce soit après coup.

**Leçon à retenir, valable au-delà de ce cas précis** : ne jamais écrire une donnée "au cas où", en comptant sur un `delete()` de secours si une vérification échoue plus tard. Toujours vérifier d'abord, écrire ensuite.

### 3e correction (remarque de la développeuse) — le stock du type varie TOUJOURS
`TypeArticle.quantite_stock` est le stock global d'un type, y compris pour les types individualisés (5 ordinateurs entrés = stock 5). La première version ne l'augmentait que pour les consommables, et la vérification de sortie lisait ce champ : une sortie d'ordinateurs aurait été bloquée à tort (stock lu = 0). Corrigé dans `services.py` : entrée → stock augmente toujours ; sortie → stock diminue toujours ; pour un type individualisé, on sélectionne en plus les `Article` concernés (avec contrôle de cohérence si moins d'articles disponibles que le stock annoncé). Limite connue : `quantite_stock` et le nombre d'`Article` disponibles peuvent se désynchroniser si on modifie le stock à la main dans l'admin.

### Question possible du jury
**"Le workflow à deux signatures que vous avez décrit (DSID puis 2ᵉ instance) — est-il implémenté ?"**
→ Réponse honnête à donner : le modèle de données le supporte déjà entièrement (table `Intervient` avec rôle et date), mais la vue API qui automatiserait ces deux étapes séparément n'est pas encore écrite — c'est la suite logique du développement, pas une lacune de conception.

---

API REST, Authentification et permissions par rôle, Frontend React, QR codes, Dashboard, Tests, Sécurité : ces parties seront documentées au fur et à mesure de leur développement, avec la même structure que le reste de ce document (ce qu'on construit → pourquoi → comment ça correspond au MCD → ce qu'il faut savoir expliquer → questions de jury possibles).

---

# 30. Limites et compromis assumés

Ce projet contient plusieurs choix pragmatiques, pas des solutions "parfaites" au sens professionnel — à connaître et à pouvoir justifier, pas à cacher :

- **`TYPE_ARTICLE ↔ ARTICLE` en relation directe**, alors qu'elle est techniquement redondante avec le chemin `ARTICLE → LIGNE_ENTREE → TYPE_ARTICLE`. Gardée pour la simplicité de lecture et d'implémentation. Conséquence : le backend doit garantir que le type d'un article est toujours cohérent avec celui de sa ligne d'entrée (pas de modification indépendante possible).
- **`TypeArticle.quantite_stock` stocké**, alors qu'il pourrait être recalculé à la volée en comptant les articles disponibles. Gardé pour la rapidité de lecture (une direction doit savoir immédiatement combien d'un produit est disponible). Conséquence : il faut une discipline stricte pour ne jamais le modifier directement, seulement via le code métier.
- **Pas de relation directe `LIGNE_BSORTIE ↔ LIGNE_SORTIE`** : le rapprochement entre demande et réalisation se fait uniquement via le `TypeArticle` commun au sein du même `BonSortie`/`Sortie`. Fonctionne tant qu'un BS n'a jamais deux lignes pour le même type — règle à faire respecter au niveau du code, pas de la base.
- **`document` en simple champ texte** pour le MVP, pas d'upload de fichier scanné — évolution possible plus tard sans casser le modèle.
- **`MOUVEMENT` sans quantité pour les articles individualisés** (implicitement 1), mais avec quantité pour les types non individualisés — deux façons de remplir la même table, distinguées par une règle applicative (`clean()`), pas par la base de données elle-même.

---

# 31. Décisions À CONFIRMER (avec Paositra)

- Format exact de génération automatique de la référence physique d'un article (exemple terrain : `101 / PAO / DSIID / LAP 31 / 01`). Non codé pour l'instant, champ libre.
- `ref_article` : pas de contrainte d'unicité tant que le format n'est pas confirmé.
- Un don doit-il obligatoirement référencer un `Fournisseur` ? Actuellement optionnel (`0,1`).
- Un Bon de Sortie peut-il donner lieu à plusieurs livraisons partielles dans le temps ? Actuellement modélisé comme une seule sortie possible par BS.

---

# 32-33. Questions possibles du jury + réponses courtes

### Métier
**Pourquoi le système ne gère-t-il pas l'acceptation administrative des demandes ?**
→ C'est une décision de périmètre : la légitimité politique/budgétaire d'une demande se décide en dehors du système ; le système ne contrôle que la disponibilité et le circuit opérationnel (autorisation DSID, validation, exécution CAME).

**Pourquoi séparer LIGNE_BSORTIE et LIGNE_SORTIE ?**
→ Parce qu'une demande peut être refusée, réduite, ou jamais exécutée. On garde une trace de ce qui a été demandé, séparément de ce qui a réellement été livré, sans jamais écraser l'un par l'autre.

**Comment savez-vous quel ordinateur précis est sorti ?**
→ Grâce à `Article` (référence individuelle, QR éventuel), lié à la `Sortie` via la relation `Sortie ↔ Article`.

**Comment savez-vous combien de cartouches sont sorties ?**
→ Via `LigneSortie.quantite_livree` et un `Mouvement` avec `type_article` + `quantite` renseignés (pas d'`Article` individuel).

### MCD / MERISE
**Pourquoi avoir gardé une relation directe TYPE_ARTICLE → ARTICLE alors qu'il existe déjà ARTICLE → LIGNE_ENTREE → TYPE_ARTICLE ?**
→ Choix pragmatique d'équipe pour simplifier la lecture du modèle et éviter une double jointure pour une question très fréquente ("quel est le type de cet article"). Assumé comme redondant, avec une règle de cohérence côté code en compensation.

**Pourquoi avez-vous modifié le MCD en cours de développement (Mouvement/Sortie) ?**
→ Parce que l'implémentation a révélé un cas métier non couvert initialement : les consommables non individualisés (`gestion_individuelle=False`) ne pouvaient pas être enregistrés dans `Mouvement`, qui exigeait un `Article` obligatoire. Corrigé après analyse, avant toute migration réelle en base.

### PostgreSQL
**Pourquoi PostgreSQL et pas MySQL ?**
→ Contrainte technique validée dès le cadrage, pour la robustesse des contraintes d'intégrité sur un vrai système de gestion.

### Django
**Pourquoi Django ?**
→ Framework mature avec ORM intégré, rapide à mettre en œuvre pour un projet de gestion avec authentification, permissions et administration.

**Pourquoi DRF (Django REST Framework) ?**
→ Parce que le frontend React communiquera avec le backend via une API REST — DRF fournit les outils standards pour ça (sérialisation, permissions, validation).

**Pourquoi AbstractUser plutôt qu'un modèle Utilisateur entièrement fait maison ?**
→ Pour bénéficier gratuitement de la gestion sécurisée des mots de passe et de la compatibilité avec le système d'authentification Django, plutôt que de réinventer cette logique (et risquer des failles de sécurité).

**Pourquoi ForeignKey ici ?**
→ Parce que plusieurs objets peuvent appartenir à un même objet parent (ex. plusieurs `Article` pour un même `TypeArticle`).

**Pourquoi PROTECT ?**
→ Pour préserver l'historique : on ne veut jamais qu'une suppression accidentelle d'un objet parent efface silencieusement les objets liés.

**Pourquoi CASCADE ici ?**
→ Parce que l'objet enfant n'a aucun sens sans son parent (une ligne de commande n'existe pas indépendamment de sa commande).

### Stock / Traçabilité
**Pourquoi quantite_stock dans TypeArticle ?**
→ Décision métier validée pour donner un accès rapide au stock global d'un type, plutôt que de recalculer à chaque consultation — compromis assumé, voir section 30.

**Que se passe-t-il si un utilisateur doit être supprimé ?**
→ Il est désactivé (`actif=False`), jamais supprimé, pour préserver la traçabilité de son historique d'opérations.

**Que se passe-t-il si une erreur est commise sur une donnée ?**
→ Principe du projet : préserver l'ancienne valeur, marquée erronée, et enregistrer une nouvelle valeur correcte avec auteur/date/motif — jamais de suppression.

---

# 34. Glossaire

| Terme | Signification |
|---|---|
| CAME | Centre d'Approvisionnement en Matériels et Équipements |
| DSID | Service qui supervise le stock et autorise les sorties |
| BS | Bon de Sortie |
| ST | Soit Transmis (document signé au moment de la réception) |
| MCD | Modèle Conceptuel de Données (schéma MERISE) |
| MERISE | Méthode de modélisation de données utilisée en France |
| ORM | Object-Relational Mapping — traduit les objets Python en lignes de base de données |
| FK / ForeignKey | Clé étrangère — référence d'une table vers une autre |
| M2M / ManyToMany | Relation plusieurs-vers-plusieurs |
| Migration | Script généré par Django décrivant un changement de structure de base de données |
| venv | Environnement virtuel Python, isolé du reste de la machine |

---

## Décision 11 — Clôture du socle Mois 1

STATUT : VALIDÉ (audité, corrigé, testé formellement dans un environnement de vérification identique à reproduire chez toi)

### Ce qui a été audité
Reprise complète du projet existant (aucune réécriture depuis zéro) : `models.py`, `services.py`, `admin.py`, `serializers.py`, `views.py`, `urls.py`, `settings.py`. Trois corrections déjà connues confirmées présentes (bug admin/`save_formset`, bug transaction `effectuer_sortie`, stock global toujours mis à jour). Deux nouveaux points corrigés à cette occasion :

### Nouvelle correction 1 — `actif` déconnecté de `is_active`
`AbstractUser` fournit déjà `is_active`, le champ que Django utilise lui-même pour bloquer la connexion d'un compte. Notre champ métier `actif` n'était relié à rien : un utilisateur désactivé pouvait quand même se connecter et agir normalement. `Utilisateur.save()` synchronise maintenant `is_active = self.actif`. Testé : désactiver `actif` bloque bien l'accès à l'API (403).

### Nouvelle correction 2 — endpoint manquant pour les lignes de Bon de Sortie
Il existait un moyen d'ajouter une ligne à une `Entree` via l'API (`/entrees/{id}/ajouter_ligne/`), mais aucun équivalent pour `BonSortie` — il fallait passer par l'admin. Ajout de `/bons-sortie/{id}/ajouter_ligne/`, symétrique, pour une API de base réellement complète sur le périmètre Mois 1 (pas d'ajout de fonctionnalité nouvelle, juste une cohérence manquante).

### Tests formels ajoutés
`inventaire/tests.py` remplace les scripts exploratoires ponctuels par une vraie suite de tests Django (`python manage.py test inventaire`), 12 tests couvrant : entrée individualisée, entrée consommable, stock global (les deux cas), sortie individualisée, sortie consommable, blocage stock insuffisant (les deux cas, y compris le cas individualisé qui était cassé avant la correction du stock global), impossibilité de sortir deux fois le même article, mouvements correctement remplis, traçabilité utilisateur + synchronisation `actif`/`is_active`, rollback complet en cas d'erreur en cours de sortie. **12/12 passent.**

### Limite connue, à garder en tête (pas un blocage Mois 1)
La sélection des articles disponibles pour une sortie (`.exclude(sorties__isnull=False)`) exclut tout article ayant déjà été sorti une fois, sans distinguer un retour réintégré — cohérent avec le fait que les retours sont hors périmètre Mois 1, mais à revoir dès que ce périmètre s'ouvrira.

---

## Décision 12 — Mois 2 : MCD révisé, workflow du Bon de Sortie ligne par ligne

STATUT : VALIDÉ (MCD final) ; trois points marqués PROPOSITION — À VALIDER ci-dessous.

### Ce qui a changé par rapport au Mois 1
- `Direction` devient `Entite` (`nom_entite`, `sigle_entite`, `type_entite` : direction / agence / dépôt). `Utilisateur.entites`, `BonSortie.entite`, `Mouvement.entite`.
- `marque` et `caracteristique` passent d'`Article` à `TypeArticle` (identiques pour tous les exemplaires d'un modèle). Unicité de `Categorie.nom_categorie` et de `(nom_type_article, categorie)`.
- `Entree.fournisseur` obligatoire. `BonSortie.utilisateur` = créateur/demandeur.
- `LigneBSortie` porte `quantite_demandee`, `quantite_autorisee`, `quantite_validee`, `etat_ligne` (demandée, autorisée, refusée, validée, rejetée, sortie).
- `Intervient` est reciblée sur `LigneBSortie`, avec `quantite_decidee` (défaut 0, un refus = 0 + motif) et `motif`.
- `LigneSortie` ne garde que `quantite_livree`, un lien `OneToOne` vers `LigneBSortie` et `type_article`. `Sortie.quantite` = somme des quantités livrées.

### Workflow (services.py)
Demande (brouillon) -> soumission -> autorisation DSID ligne par ligne -> validation DCA ligne par ligne -> sortie physique CAME.
- Statut du BS (calculé par le workflow, jamais saisi) : en attente d'autorisation, en attente de validation, validé, refusé, sorti. `REFUSE` seulement si toutes les lignes sont refusées/rejetées. Les lignes refusées/rejetées restent dans l'historique et ne bloquent pas les autres.
- Une ligne refusée par le DSID n'est jamais proposée au DCA.
- Motif obligatoire si la quantité décidée diffère de la précédente (ou en cas de refus/rejet). Chaque décision est tracée dans `Intervient` (utilisateur, date, rôle, quantité, motif).
- La Sortie physique n'est créée que pour un BS validé ; c'est la seule opération qui diminue le stock physique. Les quantités réellement livrées sont saisies par le CAME.

### Stock réservé (calculé, jamais stocké)
`réservé = Σ quantite_autorisee (lignes autorisées) + Σ quantite_validee (lignes validées)` ; `disponible pour autorisation = quantite_stock - réservé`. Si le DCA diminue 10 à 6, la réservation passe de 10 à 6 ; un rejet ou un refus la libère ; la sortie réelle la remplace par une baisse du stock physique. Les verrous de base de données (`select_for_update`) empêchent deux autorisations simultanées de réserver le même stock.

### PROPOSITION — À VALIDER (décisions que le MCD ne tranche pas)
1. Contrôle de rôle minimal : demandeur (créateur) soumet, `agent_dsid` autorise, `agent_validation` (DCA) valide, `agent_came` sort ; un superutilisateur peut tout faire. Ce n'est pas un système de permissions détaillé.
2. Le DCA ne peut pas valider plus que la quantité autorisée (sinon la réservation ne serait plus garantie).
3. Une ligne peut être livrée à 0 (non livrée, tracée dans `LigneSortie`) tant que le total livré est supérieur à 0 ; la livraison ne peut pas dépasser la quantité validée.

### Admin et API
- Admin : l'historique (Sortie, LigneSortie, Intervient, Mouvement, LigneBSortie) est en lecture seule ; `statut`, `etat_ligne`, `quantite_stock` ne sont plus modifiables à la main ; le compte connecté est l'auteur d'une entrée ou d'un BS ; les lignes d'entrée enregistrées ne se modifient ni ne se suppriment.
- API : `bons-sortie` (+ `ajouter_ligne`, `soumettre`), `lignes-bsortie` (+ `autoriser`, `valider`, filtre `?etat_ligne=`), `sorties/effectuer/`, `interventions`, `entites`, `fournisseurs`, `types-article/{id}/stock/` (physique, réservé, disponible). Plus de création directe de Sortie, Mouvement ou Article ; pas de suppression d'une Entrée.

### Migration 0006 et données de test
Les données de test du Mois 1 bloquaient réellement la migration (vérifié : deux `LigneSortie` existantes recevaient le même `ligne_bsortie`). Procédure : `purge_donnees_test.sql` (vide uniquement les tables d'opérations et remet le stock à 0, sans toucher au schéma ni aux migrations), fusion des doublons de catégories si le diagnostic en liste, puis `makemigrations` et `migrate`. `Direction` n'est pas renommée en `Entite` par Django : elle est supprimée, `Entite` est créée (aucune donnée à conserver).

### Tests
64 tests (`python manage.py test inventaire`), validés sous Django 5.2 et 6.1 : tests du Mois 1 adaptés, règles du Mois 2, API de bout en bout, pages admin. Une vérification par mutation (casser volontairement une règle) a révélé un test manquant, ajouté : un BS dont le DCA n'a validé qu'une ligne sur deux ne peut pas encore sortir.

### Limites connues
- La sélection des articles à sortir exclut tout article déjà sorti une fois : à revoir avec les retours.
- Pas encore d'écran React ni de QR codes ; les retours, corrections d'écarts et l'historique par entité restent à faire.

---

# 35. État réel d'avancement

**Socle Mois 1 considéré comme terminé et testé** : MCD complet en base PostgreSQL, logique d'entrée (individualisée et consommable), stock global correct dans les deux cas, logique de sortie avec blocage fonctionnel et transactionnel, traçabilité par `Mouvement`, admin utilisable et cohérent avec la logique métier, API REST de base (7 ressources + actions métier), authentification de base avec désactivation réellement effective, 12 tests automatisés qui passent.

**Volontairement pas commencé (Mois 2/3)** : frontend React, QR codes, dashboard, workflow complet à deux signatures (le modèle `Intervient` existe, la vue qui l'exploiterait pas encore), gestion complète des retours, système de permissions détaillé par rôle, notifications.

---

# 36. Ce qui reste à développer (Mois 2/3)

1. Frontend React connecté à l'API existante.
2. Génération et lecture de QR codes.
3. Dashboard / consultation des stocks et avoirs par direction.
4. Vue API dédiée au workflow à deux signatures (autorisation DSID puis validation 2ᵉ instance) — le modèle le supporte déjà.
5. Gestion complète des retours (contrôle avant réintégration ou mise hors service).
6. Permissions détaillées par rôle (pour l'instant, seule l'authentification de base protège l'API).
7. Corrections/écarts d'inventaire (principe validé, logique non codée).
8. Documentation finale et préparation de la soutenance de fin de stage.
