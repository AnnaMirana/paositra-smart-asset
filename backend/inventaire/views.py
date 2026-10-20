import functools

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import (
    Article, BonSortie, Categorie, Entite, Entree, Fournisseur, Intervient,
    LigneBSortie, Mouvement, Sortie, TypeArticle,
)
from .serializers import (
    ArticleSerializer, BonSortieSerializer, CategorieSerializer, DecisionLigneSerializer,
    EntiteSerializer, EntreeSerializer, FournisseurSerializer, IntervientSerializer,
    LigneBSortieInputSerializer, LigneBSortieSerializer, LigneEntreeInputSerializer,
    MouvementSerializer, SortieInputSerializer, SortieSerializer, TypeArticleSerializer,
)


def gerer_erreurs_metier(vue):
    """Traduit les erreurs levées par services.py en réponses HTTP lisibles (400 / 403)."""
    @functools.wraps(vue)
    def enveloppe(*args, **kwargs):
        try:
            return vue(*args, **kwargs)
        except DjangoValidationError as e:
            return Response({'erreur': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        except DjangoPermissionDenied as e:
            return Response({'erreur': str(e) or 'Action non autorisée.'}, status=status.HTTP_403_FORBIDDEN)
    return enveloppe


def _filtrer(queryset, request, champs):
    """Filtres simples, avec conversion explicite des paramètres booléens."""
    champs_booleens = {'gestion_individuelle'}
    for champ in champs:
        valeur = request.query_params.get(champ)
        if valeur is None or valeur == '':
            continue
        if champ in champs_booleens:
            normalisee = valeur.strip().lower()
            if normalisee in {'true', '1', 'oui'}:
                valeur = True
            elif normalisee in {'false', '0', 'non'}:
                valeur = False
            else:
                raise DRFValidationError({champ: 'Valeur booléenne invalide. Utilise true ou false.'})
        queryset = queryset.filter(**{champ: valeur})
    return queryset


class SuppressionProtegeeMixin:
    """Une donnée déjà utilisée ne se supprime pas : réponse claire au lieu d'une erreur 500."""
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'erreur': "Suppression impossible : cet élément est utilisé par d'autres données (historique conservé)."},
                status=status.HTTP_409_CONFLICT,
            )


# ----- Référentiels -----

class CategorieViewSet(SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Categorie.objects.all().order_by('nom_categorie')
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]


class FournisseurViewSet(SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all().order_by('nom_fournisseur')
    serializer_class = FournisseurSerializer
    permission_classes = [IsAuthenticated]


class EntiteViewSet(SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Entite.objects.all().order_by('nom_entite')
    serializer_class = EntiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['type_entite'])


class TypeArticleViewSet(SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = TypeArticle.objects.all().order_by('nom_type_article')
    serializer_class = TypeArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['categorie', 'gestion_individuelle'])

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        type_article = self.get_object()
        reserve = services.stock_reserve(type_article)
        return Response({
            'type_article': type_article.nom_type_article,
            'gestion_individuelle': type_article.gestion_individuelle,
            'quantite_stock': services.stock_disponible(type_article),
            'quantite_reservee': reserve,
            'stock_disponible_pour_autorisation': type_article.quantite_stock - reserve,
        })


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    # Lecture seule : un Article naît toujours d'une entrée (services.enregistrer_ligne_entree).
    queryset = Article.objects.all().order_by('id')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['type_article'])


# ----- Entrées -----

class EntreeViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                    mixins.ListModelMixin, viewsets.GenericViewSet):
    # Pas de suppression : une entrée a modifié le stock (jamais de suppression, correction tracée).
    queryset = Entree.objects.all().order_by('-id')
    serializer_class = EntreeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    @action(detail=True, methods=['post'], serializer_class=LigneEntreeInputSerializer)
    @gerer_erreurs_metier
    def ajouter_ligne(self, request, pk=None):
        entree = self.get_object()
        entree_data = self.get_serializer(data=request.data)
        entree_data.is_valid(raise_exception=True)
        type_article = entree_data.validated_data['type_article']
        quantite = entree_data.validated_data['quantite']

        ligne, articles = services.enregistrer_ligne_entree(
            entree=entree, type_article=type_article, quantite=quantite, utilisateur=request.user,
        )
        return Response({
            'ligne_id': ligne.id,
            'type_article': type_article.nom_type_article,
            'quantite': quantite,
            'gestion_individuelle': type_article.gestion_individuelle,
            'articles_crees': [a.ref_article for a in articles],
            'stock_apres': type_article.quantite_stock,
        }, status=status.HTTP_201_CREATED)


# ----- Bons de sortie (workflow) -----

class BonSortieViewSet(SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = BonSortie.objects.all().order_by('-id')
    serializer_class = BonSortieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['statut', 'entite'])

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)  # statut = brouillon par défaut

    def perform_update(self, serializer):
        if serializer.instance.statut != 'brouillon':
            raise DRFValidationError("Un bon de sortie soumis ne peut plus être modifié.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.statut != 'brouillon':
            raise DRFValidationError("Seul un brouillon peut être supprimé.")
        instance.delete()

    @action(detail=True, methods=['post'], serializer_class=LigneBSortieInputSerializer)
    def ajouter_ligne(self, request, pk=None):
        bon_sortie = self.get_object()
        if bon_sortie.statut != 'brouillon':
            return Response(
                {'erreur': "On ne peut ajouter une ligne qu'à un brouillon."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        donnees = self.get_serializer(data=request.data)
        donnees.is_valid(raise_exception=True)
        ligne = LigneBSortie.objects.create(
            bon_sortie=bon_sortie,
            type_article=donnees.validated_data['type_article'],
            quantite_demandee=donnees.validated_data['quantite_demandee'],
        )
        return Response(LigneBSortieSerializer(ligne).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], serializer_class=BonSortieSerializer)
    @gerer_erreurs_metier
    def soumettre(self, request, pk=None):
        """BROUILLON -> EN_ATTENTE_AUTORISATION (aucun corps de requête nécessaire)."""
        bon_sortie = services.soumettre_bon_sortie(self.get_object(), request.user)
        return Response(BonSortieSerializer(bon_sortie).data)


class LigneBSortieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lignes de demande. Filtres : ?bon_sortie=, ?etat_ligne=, ?type_article=.
    Le DCA ne traite que ?etat_ligne=autorisee ; une ligne refusée par le DSID ne lui est jamais proposée.
    """
    queryset = LigneBSortie.objects.select_related('bon_sortie', 'type_article').order_by('id')
    serializer_class = LigneBSortieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['bon_sortie', 'etat_ligne', 'type_article'])

    @action(detail=True, methods=['post'], serializer_class=DecisionLigneSerializer)
    @gerer_erreurs_metier
    def autoriser(self, request, pk=None):
        """DSID : quantite = quantité autorisée (0 = refus). Motif obligatoire si différente de la demande."""
        ligne = self.get_object()
        decision = self.get_serializer(data=request.data)
        decision.is_valid(raise_exception=True)
        ligne = services.autoriser_ligne(
            ligne, request.user, decision.validated_data['quantite'], decision.validated_data.get('motif', ''),
        )
        return Response(LigneBSortieSerializer(ligne).data)

    @action(detail=True, methods=['post'], serializer_class=DecisionLigneSerializer)
    @gerer_erreurs_metier
    def valider(self, request, pk=None):
        """DCA : quantite = quantité validée (0 = rejet). Motif obligatoire si différente de l'autorisation."""
        ligne = self.get_object()
        decision = self.get_serializer(data=request.data)
        decision.is_valid(raise_exception=True)
        ligne = services.valider_ligne(
            ligne, request.user, decision.validated_data['quantite'], decision.validated_data.get('motif', ''),
        )
        return Response(LigneBSortieSerializer(ligne).data)


class IntervientViewSet(viewsets.ReadOnlyModelViewSet):
    """Historique des décisions (autorisations / validations), jamais supprimé ni modifié."""
    queryset = Intervient.objects.all().order_by('-date_intervention')
    serializer_class = IntervientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['ligne_bsortie', 'role_intervention'])


# ----- Sorties -----

class SortieViewSet(viewsets.ReadOnlyModelViewSet):
    # Lecture seule : une Sortie ne se crée que par /sorties/effectuer/ (BS validé uniquement).
    queryset = Sortie.objects.all().order_by('-id')
    serializer_class = SortieSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], serializer_class=SortieInputSerializer)
    @gerer_erreurs_metier
    def effectuer(self, request):
        """CAME : sortie physique d'un BS validé. `livraisons` optionnel : quantités réellement livrées par ligne."""
        donnees = self.get_serializer(data=request.data)
        donnees.is_valid(raise_exception=True)
        try:
            bon_sortie = BonSortie.objects.get(pk=donnees.validated_data['bon_sortie'])
        except BonSortie.DoesNotExist:
            return Response({'erreur': 'Bon de sortie introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        livraisons = {
            l['ligne_bsortie']: l['quantite_livree'] for l in donnees.validated_data.get('livraisons', [])
        }
        sortie = services.effectuer_sortie(
            bon_sortie, donnees.validated_data['date_sortie'], request.user, livraisons,
        )
        return Response(SortieSerializer(sortie).data, status=status.HTTP_201_CREATED)


class MouvementViewSet(viewsets.ReadOnlyModelViewSet):
    # Lecture seule : un Mouvement est toujours la conséquence d'une opération (entrée, sortie...).
    queryset = Mouvement.objects.all().order_by('-date_mouvement', '-id')
    serializer_class = MouvementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['type_mouvement', 'article', 'type_article', 'entite'])
