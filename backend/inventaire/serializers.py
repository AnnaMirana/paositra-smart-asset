from pathlib import Path
from django.db import transaction

from rest_framework import serializers


def verifier_document(fichier):
    if not fichier:
        return fichier
    extension = Path(fichier.name).suffix.lower()
    if extension not in {'.pdf', '.jpg', '.jpeg', '.png'}:
        raise serializers.ValidationError('Format refusé. Utilisez PDF, JPG ou PNG.')
    if fichier.size > 10 * 1024 * 1024:
        raise serializers.ValidationError('Le fichier ne doit pas dépasser 10 Mo.')
    return fichier


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
    document_fichier = serializers.FileField(required=False, allow_null=True, write_only=True, validators=[verifier_document])
    document_fichier_url = serializers.SerializerMethodField()
    lignes = serializers.SerializerMethodField()
    fournisseur_nom = serializers.CharField(source='fournisseur.nom_fournisseur', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True, default=None)

    class Meta:
        model = Entree
        fields = [
            'id', 'date_entree', 'document', 'document_fichier', 'document_fichier_url', 'ref_entree', 'origine',
            'fournisseur', 'fournisseur_nom', 'utilisateur', 'utilisateur_nom', 'lignes',
        ]
        read_only_fields = ['utilisateur']

    def get_document_fichier_url(self, obj):
        request = self.context.get('request')
        if not obj.document_fichier:
            return None
        url = f'/api/entrees/{obj.pk}/document/'
        return request.build_absolute_uri(url) if request else url

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
    document_fichier = serializers.FileField(
        required=False,
        allow_null=True,
        write_only=True,
        validators=[verifier_document]
    )
    document_fichier_url = serializers.SerializerMethodField()
    lignes = LigneBSortieSerializer(many=True, read_only=True)
    entite = serializers.PrimaryKeyRelatedField(
        queryset=Entite.objects.all(),
        required=False
    )
    entite_nom = serializers.CharField(
        source='entite.nom_entite',
        read_only=True
    )
    utilisateur_nom = serializers.CharField(
        source='utilisateur.username',
        read_only=True,
        default=None
    )

    class Meta:
        model = BonSortie
        fields = [
            'id', 'reference_bs', 'document', 'document_fichier',
            'document_fichier_url', 'date_bs', 'statut',
            'entite', 'entite_nom', 'utilisateur', 'utilisateur_nom',
            'lignes',
        ]
        read_only_fields = ['statut', 'utilisateur']

    def validate(self, attrs):
        request = self.context.get('request')

        if not request:
            return attrs

        user = request.user
        role = getattr(user, 'role', '')

        if role == 'demandeur':
            entites_utilisateur = list(user.entites.all())

            if len(entites_utilisateur) != 1:
                raise serializers.ValidationError({
                    'entite': (
                        "Ce compte Demandeur doit être associé à "
                        "exactement une entité par l'administrateur."
                    )
                })

            entite_associee = entites_utilisateur[0]
            entite_transmise = attrs.get('entite')

            if entite_transmise and entite_transmise.id != entite_associee.id:
                raise serializers.ValidationError({
                    'entite': "Vous ne pouvez pas choisir une autre entité."
                })

        elif role == 'agent_direction':
            entite = attrs.get('entite')

            if entite is None and self.instance is None:
                raise serializers.ValidationError({
                    'entite': "L'agent de direction doit sélectionner une entité."
                })

        return attrs

    def get_document_fichier_url(self, obj):
        request = self.context.get('request')

        if not obj.document_fichier:
            return None

        url = f'/api/bons-sortie/{obj.pk}/document/'

        return request.build_absolute_uri(url) if request else url

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
    document_livraison = serializers.FileField(required=False, allow_null=True, write_only=True, validators=[verifier_document])
    document_livraison_url = serializers.SerializerMethodField()
    lignes = LigneSortieSerializer(many=True, read_only=True)
    bon_sortie_reference = serializers.CharField(source='bon_sortie.reference_bs', read_only=True)

    class Meta:
        model = Sortie
        fields = [
            'id', 'ref_sortie', 'date_sortie', 'quantite',
            'bon_sortie', 'bon_sortie_reference', 'articles', 'lignes',
            'document_livraison', 'document_livraison_url',
        ]
        read_only_fields = ['id', 'ref_sortie', 'date_sortie', 'quantite', 'bon_sortie',
                            'bon_sortie_reference', 'articles', 'lignes', 'document_livraison_url']

    def get_document_livraison_url(self, obj):
        request = self.context.get('request')
        if not obj.document_livraison:
            return None
        url = f'/api/sorties/{obj.pk}/preuve/'
        return request.build_absolute_uri(url) if request else url


class LivraisonInputSerializer(serializers.Serializer):
    ligne_bsortie = serializers.IntegerField()
    quantite_livree = serializers.IntegerField(min_value=0)


class SortieInputSerializer(serializers.Serializer):
    bon_sortie = serializers.IntegerField()
    date_sortie = serializers.DateField()
    document_livraison = serializers.FileField(required=True, allow_empty_file=False, validators=[verifier_document])
    livraisons = serializers.JSONField(required=False)

    def validate_livraisons(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Les livraisons doivent être une liste.')
        serializer = LivraisonInputSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


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
    entites = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Entite.objects.all(),
        required=False
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'role',
            'actif',
            'entites'
        ]
        read_only_fields = ['id', 'username']

    def validate(self, attrs):
        role = attrs.get(
            'role',
            getattr(self.instance, 'role', None)
        )

        entites = attrs.get('entites')

        if entites is None and self.instance:
            entites = list(self.instance.entites.all())

        if entites is None:
            entites = []

        if role == 'demandeur':
            if len(entites) != 1:
                raise serializers.ValidationError({
                    'entites': 'Un compte Demandeur doit être associé à exactement une entité.'
                })

            entite = entites[0]

            comptes_existants = Utilisateur.objects.filter(
                role='demandeur',
                entites=entite
            )

            if self.instance:
                comptes_existants = comptes_existants.exclude(
                    pk=self.instance.pk
                )

            if comptes_existants.exists():
                raise serializers.ValidationError({
                    'entites': 'Cette entité possède déjà un compte Demandeur.'
                })

        return attrs
    
    
class UtilisateurCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True
    )

    entites = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Entite.objects.all(),
        required=False
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'role',
            'actif',
            'entites',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        role = attrs.get('role')
        entites = attrs.get('entites', [])

        if role == 'demandeur':
            if len(entites) != 1:
                raise serializers.ValidationError({
                    'entites': 'Un compte Demandeur doit être associé à exactement une entité.'
                })

            entite = entites[0]

            compte_existant = Utilisateur.objects.filter(
                role='demandeur',
                entites=entite
            ).exists()

            if compte_existant:
                raise serializers.ValidationError({
                    'entites': 'Cette entité possède déjà un compte Demandeur.'
                })

        elif entites:
            raise serializers.ValidationError({
                'entites': 'Seuls les comptes Demandeur peuvent être associés à une entité.'
            })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        entites = validated_data.pop('entites', [])

        utilisateur = Utilisateur(**validated_data)
        utilisateur.set_password(password)
        utilisateur.save()

        utilisateur.entites.set(entites)

        return utilisateur
