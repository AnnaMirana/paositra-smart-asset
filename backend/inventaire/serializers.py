from rest_framework import serializers

from .models import (
    Article, BonSortie, Categorie, Entite, Entree, Fournisseur, Intervient,
    LigneBSortie, LigneSortie, Mouvement, Sortie, TypeArticle, Utilisateur,
)


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom_categorie']


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'nom_fournisseur', 'informations']


class EntiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entite
        fields = ['id', 'nom_entite', 'sigle_entite', 'type_entite']


class TypeArticleSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom_categorie', read_only=True)

    class Meta:
        model = TypeArticle
        fields = [
            'id', 'nom_type_article', 'marque', 'caracteristique', 'quantite_stock',
            'gestion_individuelle', 'categorie', 'categorie_nom',
        ]
        read_only_fields = ['quantite_stock']


class ArticleSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(source='type_article.nom_type_article', read_only=True)
    marque = serializers.CharField(source='type_article.marque', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'ref_article', 'num_serie', 'qr_code', 'type_article',
            'type_article_nom', 'marque', 'ligne_entree',
        ]
        read_only_fields = fields


# ----- Entrées -----

class LigneEntreeInputSerializer(serializers.Serializer):
    type_article = serializers.PrimaryKeyRelatedField(queryset=TypeArticle.objects.all())
    quantite = serializers.IntegerField(min_value=1)


class EntreeSerializer(serializers.ModelSerializer):
    lignes = serializers.SerializerMethodField()
    fournisseur_nom = serializers.CharField(source='fournisseur.nom_fournisseur', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True, default=None)

    class Meta:
        model = Entree
        fields = [
            'id', 'date_entree', 'document', 'ref_entree', 'origine',
            'fournisseur', 'fournisseur_nom', 'utilisateur', 'utilisateur_nom', 'lignes',
        ]
        read_only_fields = ['utilisateur']

    def get_lignes(self, obj):
        return [
            {
                'id': l.id,
                'type_article_id': l.type_article.id,
                'type_article': l.type_article.nom_type_article,
                'quantite': l.quantite,
            }
            for l in obj.lignes.all()
        ]


# ----- Workflow du Bon de Sortie -----

class IntervientSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)

    class Meta:
        model = Intervient
        fields = [
            'id', 'ligne_bsortie', 'role_intervention', 'utilisateur', 'utilisateur_nom',
            'date_intervention', 'quantite_decidee', 'motif',
        ]
        read_only_fields = fields


class LigneBSortieSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(source='type_article.nom_type_article', read_only=True)
    bon_sortie_reference = serializers.CharField(source='bon_sortie.reference_bs', read_only=True)
    interventions = IntervientSerializer(many=True, read_only=True)

    class Meta:
        model = LigneBSortie
        fields = [
            'id', 'bon_sortie', 'bon_sortie_reference', 'type_article', 'type_article_nom',
            'quantite_demandee', 'quantite_autorisee', 'quantite_validee', 'etat_ligne',
            'interventions',
        ]
        read_only_fields = ['bon_sortie', 'quantite_autorisee', 'quantite_validee', 'etat_ligne']


class LigneBSortieInputSerializer(serializers.Serializer):
    type_article = serializers.PrimaryKeyRelatedField(queryset=TypeArticle.objects.all())
    quantite_demandee = serializers.IntegerField(min_value=1)


class BonSortieSerializer(serializers.ModelSerializer):
    lignes = LigneBSortieSerializer(many=True, read_only=True)
    entite_nom = serializers.CharField(source='entite.nom_entite', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True, default=None)

    class Meta:
        model = BonSortie
        fields = [
            'id', 'reference_bs', 'document', 'date_bs', 'statut',
            'entite', 'entite_nom', 'utilisateur', 'utilisateur_nom', 'lignes',
        ]
        read_only_fields = ['statut', 'utilisateur']


class DecisionLigneSerializer(serializers.Serializer):
    """Décision du DSID (autoriser) ou du DCA (valider) sur une ligne. quantite = 0 : refus / rejet."""
    quantite = serializers.IntegerField(min_value=0)
    motif = serializers.CharField(required=False, allow_blank=True)


# ----- Sorties -----

class LigneSortieSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(source='type_article.nom_type_article', read_only=True)

    class Meta:
        model = LigneSortie
        fields = ['id', 'ligne_bsortie', 'type_article', 'type_article_nom', 'quantite_livree']
        read_only_fields = fields


class SortieSerializer(serializers.ModelSerializer):
    lignes = LigneSortieSerializer(many=True, read_only=True)
    bon_sortie_reference = serializers.CharField(source='bon_sortie.reference_bs', read_only=True)

    class Meta:
        model = Sortie
        fields = [
            'id', 'ref_sortie', 'date_sortie', 'quantite',
            'bon_sortie', 'bon_sortie_reference', 'articles', 'lignes',
        ]
        read_only_fields = fields


class LivraisonInputSerializer(serializers.Serializer):
    ligne_bsortie = serializers.IntegerField()
    quantite_livree = serializers.IntegerField(min_value=0)


class SortieInputSerializer(serializers.Serializer):
    bon_sortie = serializers.IntegerField()
    date_sortie = serializers.DateField()
    livraisons = LivraisonInputSerializer(many=True, required=False)


class MouvementSerializer(serializers.ModelSerializer):
    cible = serializers.SerializerMethodField()
    entite_nom = serializers.CharField(source='entite.nom_entite', read_only=True, default=None)
    type_article_nom = serializers.CharField(source='type_article.nom_type_article', read_only=True, default=None)
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True, default=None)
    utilisateur_details = serializers.SerializerMethodField()

    class Meta:
        model = Mouvement
        fields = [
            'id', 'type_mouvement', 'article', 'type_article', 'type_article_nom',
            'quantite', 'cible', 'utilisateur', 'utilisateur_nom',
            'utilisateur_nom_saisi', 'utilisateur_role_saisi', 'utilisateur_details',
            'operation_ref', 'entite', 'entite_nom', 'date_mouvement',
        ]
        read_only_fields = fields

    def get_cible(self, obj):
        if obj.article:
            return f"Article {obj.article.ref_article}"
        return f"{obj.quantite} x {obj.type_article}"

    def get_utilisateur_details(self, obj):
        if not obj.utilisateur:
            return None
        nom_saisi = obj.utilisateur_nom_saisi.strip()
        role_saisi = obj.utilisateur_role_saisi.strip()
        return {
            'first_name': obj.utilisateur.first_name,
            'last_name': obj.utilisateur.last_name,
            'nom_complet': nom_saisi or obj.utilisateur.get_full_name() or obj.utilisateur.username,
            'role': obj.utilisateur.role,
            'role_libelle': role_saisi or obj.utilisateur.get_role_display(),
        }


class UtilisateurProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id', 'username', 'role']
