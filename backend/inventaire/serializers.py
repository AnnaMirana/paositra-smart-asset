from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

from rest_framework import serializers

from .models import (
    Article,
    BonSortie,
    Categorie,
    Entite,
    Entree,
    Fournisseur,
    Intervient,
    LigneBSortie,
    LigneEntree,
    Mouvement,
    Sortie,
    TypeArticle,
    Utilisateur,
)


# ---------------------------------------------------------------------------
# Validation des fichiers transmis
# ---------------------------------------------------------------------------

def verifier_document(fichier):
    """Contrôle minimal du nom, du type déclaré et de la taille d'un document."""
    if not fichier:
        return

    extensions_autorisees = {'.pdf', '.png', '.jpg', '.jpeg'}
    extension = Path(fichier.name).suffix.lower()

    if extension not in extensions_autorisees:
        raise serializers.ValidationError(
            "Format non autorisé. Utilisez un fichier PDF, PNG ou JPG."
        )

    taille_max = 10 * 1024 * 1024
    if fichier.size > taille_max:
        raise serializers.ValidationError(
            "Le fichier dépasse la taille maximale autorisée de 10 Mo."
        )


# ---------------------------------------------------------------------------
# Référentiels
# ---------------------------------------------------------------------------

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
    categorie_nom = serializers.CharField(
        source='categorie.nom_categorie', read_only=True
    )
    stock_physique = serializers.IntegerField(
        source='quantite_stock', read_only=True
    )
    stock_reserve = serializers.SerializerMethodField()
    stock_disponible_pour_autorisation = serializers.SerializerMethodField()

    class Meta:
        model = TypeArticle
        fields = [
            'id', 'nom_type_article', 'categorie', 'categorie_nom',
            'marque', 'caracteristique', 'gestion_individuelle',
            'quantite_stock', 'stock_physique', 'stock_reserve',
            'stock_disponible_pour_autorisation',
        ]
        read_only_fields = [
            'quantite_stock', 'stock_physique', 'stock_reserve',
            'stock_disponible_pour_autorisation',
        ]

    def get_stock_reserve(self, obj):
        from . import services
        return services.stock_reserve(obj)

    def get_stock_disponible_pour_autorisation(self, obj):
        from . import services
        return services.stock_disponible_pour_autorisation(obj)


class ArticleSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(
        source='type_article.nom_type_article', read_only=True
    )
    categorie_nom = serializers.CharField(
        source='type_article.categorie.nom_categorie', read_only=True
    )

    class Meta:
        model = Article
        fields = [
            'id', 'ref_article', 'qr_code', 'num_serie',
            'type_article', 'type_article_nom', 'categorie_nom',
            'ligne_entree',
        ]


# ---------------------------------------------------------------------------
# Entrées en stock
# ---------------------------------------------------------------------------

class LigneEntreeSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(
        source='type_article.nom_type_article', read_only=True
    )

    class Meta:
        model = LigneEntree
        fields = ['id', 'quantite', 'type_article', 'type_article_nom']


class LigneEntreeInputSerializer(serializers.Serializer):
    type_article = serializers.PrimaryKeyRelatedField(
        queryset=TypeArticle.objects.all()
    )
    quantite = serializers.IntegerField(min_value=1)


class EntreeSerializer(serializers.ModelSerializer):
    lignes = LigneEntreeSerializer(many=True, read_only=True)
    fournisseur_nom = serializers.CharField(
        source='fournisseur.nom_fournisseur', read_only=True
    )
    utilisateur_nom = serializers.SerializerMethodField()

    def get_utilisateur_nom(self, obj):
        return obj.utilisateur.get_full_name().strip() or obj.utilisateur.username

    class Meta:
        model = Entree
        fields = [
            'id', 'date_entree', 'ref_entree', 'origine',
            'fournisseur', 'fournisseur_nom', 'document',
            'document_fichier', 'utilisateur', 'utilisateur_nom', 'lignes',
        ]
        read_only_fields = ['id', 'utilisateur', 'lignes']

    def validate(self, attrs):
        origine = attrs.get('origine', getattr(self.instance, 'origine', None))
        fournisseur = attrs.get(
            'fournisseur',
            getattr(self.instance, 'fournisseur', None)
        )
        if origine == 'achat' and fournisseur is None:
            raise serializers.ValidationError({
                'fournisseur': "Un fournisseur est obligatoire pour un achat."
            })
        return attrs


# ---------------------------------------------------------------------------
# Bons de sortie et décisions ligne par ligne
# ---------------------------------------------------------------------------

class LigneBSortieSerializer(serializers.ModelSerializer):
    type_article_nom = serializers.CharField(
        source='type_article.nom_type_article', read_only=True
    )
    etat_ligne_libelle = serializers.CharField(
        source='get_etat_ligne_display', read_only=True
    )

    class Meta:
        model = LigneBSortie
        fields = [
            'id', 'bon_sortie', 'type_article', 'type_article_nom',
            'quantite_demandee', 'quantite_autorisee',
            'quantite_validee', 'etat_ligne', 'etat_ligne_libelle',
        ]
        read_only_fields = [
            'bon_sortie', 'quantite_autorisee', 'quantite_validee',
            'etat_ligne',
        ]


class LigneBSortieInputSerializer(serializers.Serializer):
    type_article = serializers.PrimaryKeyRelatedField(
        queryset=TypeArticle.objects.all()
    )
    quantite_demandee = serializers.IntegerField(min_value=1)


class DecisionLigneSerializer(serializers.Serializer):
    quantite = serializers.IntegerField(min_value=0)
    motif = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class BonSortieSerializer(serializers.ModelSerializer):
    lignes = LigneBSortieSerializer(many=True, read_only=True)
    entite_nom = serializers.CharField(
        source='entite.nom_entite', read_only=True
    )
    utilisateur_nom = serializers.SerializerMethodField()
    statut_libelle = serializers.CharField(
        source='get_statut_display', read_only=True
    )
    autorite_choisie_libelle = serializers.CharField(
        source='get_autorite_choisie_display', read_only=True, allow_null=True
    )
    autorite_choisie_par_nom = serializers.SerializerMethodField()

    def get_autorite_choisie_par_nom(self, obj):
        if not obj.autorite_choisie_par:
            return None
        return obj.autorite_choisie_par.get_full_name().strip() or obj.autorite_choisie_par.username

    def get_utilisateur_nom(self, obj):
        return obj.utilisateur.get_full_name().strip() or obj.utilisateur.username

    class Meta:
        model = BonSortie
        fields = [
            'id', 'reference_bs', 'date_bs', 'statut', 'statut_libelle',
            'document', 'document_fichier', 'entite', 'entite_nom',
            'utilisateur', 'utilisateur_nom', 'lignes',
            'autorite_choisie', 'autorite_choisie_libelle',
            'autorite_choisie_par', 'autorite_choisie_par_nom', 'autorite_choisie_le',
        ]
        read_only_fields = [
            'id', 'statut', 'utilisateur', 'lignes', 'autorite_choisie',
            'autorite_choisie_par', 'autorite_choisie_le',
        ]


class IntervientSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name', read_only=True
    )
    role_intervention_libelle = serializers.CharField(
        source='get_role_intervention_display', read_only=True
    )

    class Meta:
        model = Intervient
        fields = [
            'id', 'ligne_bsortie', 'utilisateur', 'utilisateur_nom',
            'role_intervention', 'role_intervention_libelle',
            'date_intervention', 'quantite_decidee', 'motif',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Sorties physiques et mouvements
# ---------------------------------------------------------------------------

class LivraisonLigneInputSerializer(serializers.Serializer):
    ligne_bsortie = serializers.IntegerField(min_value=1)
    quantite_livree = serializers.IntegerField(min_value=0)


class SortieInputSerializer(serializers.Serializer):
    bon_sortie = serializers.PrimaryKeyRelatedField(
        queryset=BonSortie.objects.all()
    )
    date_sortie = serializers.DateField()
    livraisons = LivraisonLigneInputSerializer(many=True, required=False)
    document_livraison = serializers.FileField(
        required=False, allow_null=True
    )

    def to_internal_value(self, data):
        # En multipart/form-data, la liste des livraisons arrive souvent
        # sous forme de chaîne JSON. Il faut convertir QueryDict en dict
        # classique avant d'y placer la liste Python décodée.
        if hasattr(data, 'getlist'):
            data = {key: data.get(key) for key in data.keys()}
        elif hasattr(data, 'copy'):
            data = data.copy()

        livraisons = data.get('livraisons') if hasattr(data, 'get') else None
        if isinstance(livraisons, str):
            try:
                data['livraisons'] = json.loads(livraisons)
            except json.JSONDecodeError:
                raise serializers.ValidationError({
                    'livraisons': 'Le format des livraisons doit être une liste JSON valide.'
                })
        return super().to_internal_value(data)

    def validate_document_livraison(self, value):
        verifier_document(value)
        return value


class SortieSerializer(serializers.ModelSerializer):
    bon_sortie_reference = serializers.CharField(
        source='bon_sortie.reference_bs', read_only=True
    )
    lignes = serializers.SerializerMethodField()
    articles_refs = serializers.SerializerMethodField()

    class Meta:
        model = Sortie
        fields = [
            'id', 'date_sortie', 'ref_sortie', 'quantite',
            'bon_sortie', 'bon_sortie_reference',
            'document_livraison', 'lignes', 'articles', 'articles_refs',
        ]
        read_only_fields = fields

    def get_lignes(self, obj):
        return [
            {
                'id': ligne.id,
                'ligne_bsortie': ligne.ligne_bsortie_id,
                'type_article': ligne.type_article_id,
                'type_article_nom': ligne.type_article.nom_type_article,
                'quantite_livree': ligne.quantite_livree,
            }
            for ligne in obj.lignes.select_related('type_article')
        ]

    def get_articles_refs(self, obj):
        return list(obj.articles.values_list('ref_article', flat=True))


class MouvementSerializer(serializers.ModelSerializer):
    article_ref = serializers.CharField(
        source='article.ref_article',
        read_only=True,
        allow_null=True
    )
    type_article_nom = serializers.CharField(
        source='type_article.nom_type_article',
        read_only=True,
        allow_null=True
    )
    utilisateur_nom = serializers.SerializerMethodField()

    def get_utilisateur_nom(self, obj):
        nom_snapshot = (obj.utilisateur_nom_saisi or '').strip()
        if nom_snapshot and nom_snapshot != 'Nom non renseigné':
            return nom_snapshot
        if obj.utilisateur:
            return obj.utilisateur.get_full_name().strip() or obj.utilisateur.username
        return nom_snapshot or 'Nom non renseigné'
    entite_nom = serializers.CharField(
        source='entite.nom_entite',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Mouvement
        fields = [
            'id', 'date_mouvement', 'type_mouvement',
            'article', 'article_ref', 'type_article', 'type_article_nom',
            'quantite', 'utilisateur', 'utilisateur_nom_saisi',
            'utilisateur_nom', 'utilisateur_role_saisi', 'operation_ref', 'entite',
            'entite_nom',
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Comptes utilisateurs
# ---------------------------------------------------------------------------

class UtilisateurProfileSerializer(serializers.ModelSerializer):
    entites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Entite.objects.all(), required=False
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'actif', 'entites',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        role = attrs.get('role', getattr(self.instance, 'role', None))
        entites = attrs.get('entites')
        if entites is None:
            entites = list(self.instance.entites.all()) if self.instance else []

        if role == 'demandeur' and len(entites) != 1:
            raise serializers.ValidationError({
                'entites': "Un compte Demandeur doit être associé à exactement une entité."
            })
        if role != 'demandeur' and entites:
            raise serializers.ValidationError({
                'entites': "Seuls les comptes Demandeur peuvent être associés à une entité."
            })
        return attrs


class UtilisateurCreationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    entites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Entite.objects.all(), required=False
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'actif', 'entites',
        ]
        read_only_fields = ['id', 'actif']

    def validate_email(self, value):
        value = value.strip().lower()
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Cette adresse e-mail est déjà utilisée."
            )
        return value

    def validate(self, attrs):
        role = attrs.get('role')
        entites = attrs.get('entites', [])
        if role == 'demandeur' and len(entites) != 1:
            raise serializers.ValidationError({
                'entites': "Un compte Demandeur doit être associé à exactement une entité."
            })
        if role != 'demandeur' and entites:
            raise serializers.ValidationError({
                'entites': "Seuls les comptes Demandeur peuvent être associés à une entité."
            })
        return attrs

    def create(self, validated_data):
        import secrets
        import string
        from datetime import timedelta

        from django.conf import settings
        from django.core.mail import send_mail
        from django.db import transaction
        from django.utils import timezone
        from django.utils.text import slugify

        entites = validated_data.pop('entites', [])
        first_name = validated_data['first_name'].strip()
        last_name = validated_data['last_name'].strip()
        email = validated_data['email']

        base = slugify(f'{first_name}.{last_name}') or email.split('@')[0]
        base = base[:140]
        username = base
        suffix = 1
        while Utilisateur.objects.filter(username=username).exists():
            suffix += 1
            suffix_text = str(suffix)
            username = f'{base[:150-len(suffix_text)]}{suffix_text}'

        alphabet = string.ascii_letters + string.digits + '!@#$%_-'
        temporary_password = ''.join(
            secrets.choice(alphabet) for _ in range(20)
        )

        with transaction.atomic():
            utilisateur = Utilisateur(**validated_data)
            utilisateur.username = username
            utilisateur.actif = True
            utilisateur.is_active = True
            utilisateur.doit_changer_mot_de_passe = True
            utilisateur.mot_de_passe_temporaire_expire_le = (
                timezone.now() + timedelta(hours=24)
            )
            utilisateur.set_password(temporary_password)
            utilisateur.save()
            utilisateur.entites.set(entites)

            sujet = 'Votre compte PAOSITRA SMART ASSET'
            message = (
                f'Bonjour {first_name} {last_name},\n\n'
                'Votre compte PAOSITRA SMART ASSET a été créé.\n\n'
                f'Nom de connexion : {first_name} {last_name}\n'
                f'Mot de passe temporaire : {temporary_password}\n\n'
                'Ce mot de passe expire dans 24 heures. '
                'Lors de votre première connexion, vous devrez choisir un nouveau mot de passe.\n\n'
                'Ne partagez pas ces informations.\n'
            )

        try:
            sent = send_mail(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )

            if sent != 1:
                raise RuntimeError('Envoi du message non confirmé.')

        except Exception:
            logger.exception(
                "Échec de l'envoi du mot de passe temporaire à %s",
                email
            )

            utilisateur.delete()

            raise serializers.ValidationError({
                'email': "Le compte n'a pas été créé car l'envoi du mot de passe temporaire a échoué."
            })

        return utilisateur