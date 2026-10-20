from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('agent_dsid', 'Agent DSID'),
        ('agent_validation', 'Agent de validation (DCA)'),
        ('agent_came', 'Agent CAME'),
        ('demandeur', 'Demandeur'),
        ('agent_direction', 'Agent de direction'),
        ('auditeur', 'Auditeur'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    actif = models.BooleanField(default=True)
    entites = models.ManyToManyField('Entite', related_name='utilisateurs', blank=True)

    def save(self, *args, **kwargs):
        # is_active est le champ que Django utilise réellement pour bloquer une connexion.
        self.is_active = self.actif
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Categorie(models.Model):
    nom_categorie = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom_categorie


class Fournisseur(models.Model):
    nom_fournisseur = models.CharField(max_length=150)
    informations = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom_fournisseur


class Entite(models.Model):
    """
    Remplace DIRECTION (Mois 2). Référentiel général des structures de
    Paositra : directions, agences, dépôts (dont le CAME). L'existence
    d'une ENTITE ne décide pas qui peut demander/recevoir une sortie —
    ce sera une règle applicative, pas une contrainte du MCD.
    """
    TYPE_ENTITE_CHOICES = [
        ('direction', 'Direction'),
        ('agence', 'Agence'),
        ('depot', 'Dépôt'),
    ]

    nom_entite = models.CharField(max_length=150)
    sigle_entite = models.CharField(max_length=30, blank=True, null=True)
    type_entite = models.CharField(max_length=20, choices=TYPE_ENTITE_CHOICES)

    def __str__(self):
        return f"{self.nom_entite} ({self.sigle_entite})" if self.sigle_entite else self.nom_entite


class TypeArticle(models.Model):
    nom_type_article = models.CharField(max_length=150)
    quantite_stock = models.PositiveIntegerField(default=0)
    gestion_individuelle = models.BooleanField(default=False)
    # Déplacés depuis ARTICLE (Mois 2) : identiques pour tous les exemplaires d'un même modèle.
    marque = models.CharField(max_length=150, blank=True, null=True)
    caracteristique = models.TextField(blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='types_article')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nom_type_article', 'categorie'], name='unique_type_par_categorie')
        ]

    def __str__(self):
        return self.nom_type_article


class Entree(models.Model):
    ORIGINE_CHOICES = [
        ('achat', 'Achat'),
        ('don', 'Don'),
    ]

    date_entree = models.DateField()
    document = models.CharField(max_length=255, blank=True, null=True)
    ref_entree = models.CharField(max_length=100, unique=True)
    origine = models.CharField(max_length=20, choices=ORIGINE_CHOICES)

    # Fournisseur obligatoire (Mois 2).
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name='entrees')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='entrees_enregistrees')

    def __str__(self):
        return f"Entrée {self.ref_entree} du {self.date_entree}"


class LigneEntree(models.Model):
    quantite = models.PositiveIntegerField()

    entree = models.ForeignKey(Entree, on_delete=models.CASCADE, related_name='lignes')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_entree')

    def __str__(self):
        return f"{self.quantite} x {self.type_article} (Entrée {self.entree.ref_entree})"


class Article(models.Model):
    qr_code = models.CharField(max_length=255, unique=True, blank=True, null=True)
    num_serie = models.CharField(max_length=150, blank=True, null=True)
    ref_article = models.CharField(max_length=150)
    # marque et caracteristique retirés (Mois 2) -> déplacés vers TypeArticle.

    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='articles')
    ligne_entree = models.ForeignKey(LigneEntree, on_delete=models.PROTECT, related_name='articles')

    def __str__(self):
        return self.ref_article


class BonSortie(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_attente_autorisation', "En attente d'autorisation"),
        ('en_attente_validation', 'En attente de validation'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
        ('sorti', 'Sorti'),
    ]

    reference_bs = models.CharField(max_length=100, unique=True)
    document = models.CharField(max_length=255, blank=True, null=True)
    date_bs = models.DateField()
    # Géré automatiquement par le workflow (Mois 2) — jamais modifié à la main.
    # REFUSE seulement si TOUTES les lignes finissent refusées/rejetées.
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='brouillon')

    entite = models.ForeignKey(Entite, on_delete=models.PROTECT, related_name='bons_sortie')
    # Créateur/demandeur (Mois 2, relation qui manquait au Mois 1).
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='bons_sortie_crees')

    def __str__(self):
        return self.reference_bs


class LigneBSortie(models.Model):
    ETAT_CHOICES = [
        ('demandee', 'Demandée'),
        ('autorisee', 'Autorisée'),
        ('refusee', 'Refusée'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée'),
        ('sortie', 'Sortie'),
    ]

    quantite_demandee = models.PositiveIntegerField()
    quantite_autorisee = models.PositiveIntegerField(blank=True, null=True)
    quantite_validee = models.PositiveIntegerField(blank=True, null=True)
    # Géré automatiquement par le workflow (Mois 2) — jamais modifié à la main.
    etat_ligne = models.CharField(max_length=20, choices=ETAT_CHOICES, default='demandee')

    bon_sortie = models.ForeignKey(BonSortie, on_delete=models.CASCADE, related_name='lignes')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_bsortie')

    def __str__(self):
        return f"{self.quantite_demandee} x {self.type_article} (BS {self.bon_sortie.reference_bs})"


class Intervient(models.Model):
    """
    Reciblée vers LIGNE_BSORTIE (Mois 2) : les décisions se prennent
    maintenant ligne par ligne, pas au niveau du BonSortie entier.
    """
    ROLE_CHOICES = [
        ('autorisation', 'Autorisation DSID'),
        ('validation', 'Validation DCA'),
    ]

    ligne_bsortie = models.ForeignKey(LigneBSortie, on_delete=models.CASCADE, related_name='interventions')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='interventions')
    role_intervention = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_intervention = models.DateTimeField(auto_now_add=True)
    # Non nullable, défaut 0 : un refus s'enregistre avec quantite_decidee=0 + motif.
    quantite_decidee = models.PositiveIntegerField(default=0)
    motif = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.utilisateur} — {self.role_intervention} sur {self.ligne_bsortie}"


class LigneSortie(models.Model):
    """
    Simplifiée (Mois 2) : ne porte plus que quantite_livree.
    quantite_demandee/autorisee vivent sur LigneBSortie, reliée directement
    ci-dessous — plus besoin de les dupliquer ici.
    """
    quantite_livree = models.PositiveIntegerField()

    sortie = models.ForeignKey('Sortie', on_delete=models.CASCADE, related_name='lignes')
    # Lien direct ajouté (Mois 2) : une ligne de sortie correspond toujours
    # exactement à une ligne de demande d'origine.
    ligne_bsortie = models.OneToOneField(LigneBSortie, on_delete=models.PROTECT, related_name='ligne_sortie')
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='lignes_sortie')

    def __str__(self):
        return f"{self.type_article} — livré {self.quantite_livree}"


class Sortie(models.Model):
    date_sortie = models.DateField()
    # Maintenu automatiquement = somme des LigneSortie.quantite_livree liées (logique dans services.py).
    quantite = models.PositiveIntegerField()
    ref_sortie = models.CharField(max_length=100, unique=True)

    bon_sortie = models.OneToOneField(BonSortie, on_delete=models.PROTECT, related_name='sortie')
    articles = models.ManyToManyField(Article, related_name='sorties')

    def __str__(self):
        return f"Sortie {self.ref_sortie}"


class Mouvement(models.Model):
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée en stock'),
        ('sortie', 'Sortie'),
        ('retour', 'Retour'),
        ('controle_retour', 'Contrôle de retour'),
        ('reintegration', 'Réintégration en stock'),
        ('mise_hors_service', 'Mise hors service'),
        ('perte', 'Perte déclarée'),
        ('correction', 'Correction'),
    ]

    date_mouvement = models.DateTimeField(auto_now_add=True)
    type_mouvement = models.CharField(max_length=30, choices=TYPE_MOUVEMENT_CHOICES)

    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
    type_article = models.ForeignKey(TypeArticle, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)
    quantite = models.PositiveIntegerField(null=True, blank=True)

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='mouvements_enregistres')
    entite = models.ForeignKey(Entite, on_delete=models.PROTECT, related_name='mouvements', null=True, blank=True)

    def clean(self):
        if self.article and self.type_article:
            raise ValidationError(
                "Un mouvement ne peut pas concerner à la fois un article individualisé et un type par quantité."
            )
        if not self.article and not self.type_article:
            raise ValidationError(
                "Un mouvement doit concerner soit un article, soit un type_article — jamais aucun des deux."
            )
        if self.type_article and not self.quantite:
            raise ValidationError(
                "La quantité est obligatoire pour un mouvement portant sur un type_article."
            )
        if self.article and self.quantite:
            raise ValidationError(
                "La quantité ne doit pas être renseignée pour un mouvement d'article individualisé (elle vaut 1 implicitement)."
            )

    def __str__(self):
        cible = self.article if self.article else f"{self.quantite} x {self.type_article}"
        return f"{self.type_mouvement} — {cible} ({self.date_mouvement:%Y-%m-%d})"
