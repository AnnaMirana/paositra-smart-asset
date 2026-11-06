import functools

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from django.http import HttpResponse, FileResponse, Http404
import mimetypes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from . import services
from .models import (
    Article, BonSortie, Categorie, Entite, Entree, Fournisseur, Intervient,
    LigneBSortie, Mouvement, Sortie, TypeArticle, Utilisateur,  # <-- S'assurer que Utilisateur est importé
)
from .serializers import (
    ArticleSerializer, BonSortieSerializer, CategorieSerializer, DecisionLigneSerializer,
    EntiteSerializer, EntreeSerializer, FournisseurSerializer, IntervientSerializer,
    LigneBSortieInputSerializer, LigneBSortieSerializer, LigneEntreeInputSerializer,
    MouvementSerializer, SortieInputSerializer, SortieSerializer, TypeArticleSerializer,
    UtilisateurProfileSerializer, verifier_document,  UtilisateurCreationSerializer,# validation des pièces jointes
)

from rest_framework import serializers

    
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


def _role(user):
    return getattr(user, 'role', '')


def _est_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or _role(user) == 'admin'))


def _reponse_fichier(fichier):
    if not fichier:
        raise Http404('Document non disponible.')
    try:
        fichier.open('rb')
    except (FileNotFoundError, OSError):
        raise Http404('Fichier introuvable sur le stockage.')
    nom = fichier.name.rsplit('/', 1)[-1]
    content_type = mimetypes.guess_type(nom)[0] or 'application/octet-stream'
    return FileResponse(fichier, as_attachment=False, filename=nom, content_type=content_type)


def _exiger_roles(request, *roles):
    user = request.user
    if not user.is_authenticated or not getattr(user, 'actif', True):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Compte inactif ou non authentifié.')
    if not (_est_admin(user) or _role(user) in roles):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Votre rôle ne permet pas cette action.')


class ExporterMixin:
    """Exports Excel/PDF basés sur le queryset déjà filtré par les permissions."""
    def _lignes_export(self):
        serializer = self.get_serializer(self.filter_queryset(self.get_queryset()), many=True)
        data = serializer.data
        if not data:
            return ['Aucun résultat'], []
        colonnes = list(data[0].keys())
        def valeur_export(value):
            texte = str(value if value is not None else '')
            # Évite l'injection de formules Excel via les valeurs textuelles.
            if texte.startswith(('=', '+', '-', '@')):
                texte = "'" + texte
            return texte
        lignes = [[valeur_export(item.get(c, '')) for c in colonnes] for item in data]
        return colonnes, lignes

    @action(detail=False, methods=['get'], url_path='export-excel')
    def export_excel(self, request):
        from openpyxl import Workbook
        colonnes, lignes = self._lignes_export()
        wb = Workbook()
        ws = wb.active
        ws.title = 'Export'
        ws.append(colonnes)
        for ligne in lignes:
            ws.append(ligne)
        for col in ws.columns:
            largeur = min(max(max(len(str(c.value or '')) for c in col) + 2, 12), 45)
            ws.column_dimensions[col[0].column_letter].width = largeur
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{self.basename if hasattr(self, "basename") else "export"}.xlsx"'
        wb.save(response)
        return response

    @action(detail=False, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm
        from io import BytesIO
        colonnes, lignes = self._lignes_export()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm)
        styles = getSampleStyleSheet()
        contenu = [Paragraph('PAOSITRA SMART ASSET — Export', styles['Title']), Spacer(1, 6*mm)]
        def pdf_safe(value):
            return str(value).encode('latin-1', 'replace').decode('latin-1')
        data = [[pdf_safe(c) for c in colonnes]] + [[pdf_safe(v) for v in ligne] for ligne in lignes]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17365D')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.35,colors.grey),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#EEF3F8')])]))
        contenu.append(table)
        doc.build(contenu)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.basename if hasattr(self, "basename") else "export"}.pdf"'
        return response


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

class CategorieViewSet(ExporterMixin, SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Categorie.objects.all().order_by('nom_categorie')
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]

    def _controle_ecriture(self):
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            _exiger_roles(self.request, 'admin')

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._controle_ecriture()


class FournisseurViewSet(ExporterMixin, SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all().order_by('nom_fournisseur')
    serializer_class = FournisseurSerializer
    permission_classes = [IsAuthenticated]

    def _controle_ecriture(self):
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            _exiger_roles(self.request, 'admin')

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._controle_ecriture()


class EntiteViewSet(ExporterMixin, SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = Entite.objects.all().order_by('nom_entite')
    serializer_class = EntiteSerializer
    permission_classes = [IsAuthenticated]

    def _controle_ecriture(self):
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            _exiger_roles(self.request, 'admin')

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._controle_ecriture()

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['type_entite'])


class TypeArticleViewSet(ExporterMixin, SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = TypeArticle.objects.all().order_by('nom_type_article')
    serializer_class = TypeArticleSerializer
    permission_classes = [IsAuthenticated]

    def _controle_ecriture(self):
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            _exiger_roles(self.request, 'admin')

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._controle_ecriture()

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['categorie', 'gestion_individuelle'])

    def _lignes_export(self):
        types = self.filter_queryset(self.get_queryset())
        colonnes = ['id', 'nom_type_article', 'categorie', 'marque', 'gestion_individuelle',
                    'stock_physique', 'stock_reserve', 'stock_disponible_pour_autorisation']
        lignes = []
        for t in types:
            reserve = services.stock_reserve(t)
            lignes.append([str(t.id), t.nom_type_article, t.categorie.nom_categorie, t.marque or '',
                           'Oui' if t.gestion_individuelle else 'Non', str(t.quantite_stock), str(reserve),
                           str(t.quantite_stock - reserve)])
        return colonnes, lignes

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


class ArticleViewSet(ExporterMixin, viewsets.ReadOnlyModelViewSet):
    # Lecture seule : un Article naît toujours d'une entrée (services.enregistrer_ligne_entree).
    queryset = Article.objects.all().order_by('id')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _filtrer(super().get_queryset(), self.request, ['type_article'])


# ----- Entrées -----

class EntreeViewSet(ExporterMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                    mixins.ListModelMixin, viewsets.GenericViewSet):
    # Pas de suppression : une entrée a modifié le stock (jamais de suppression, correction tracée).
    queryset = Entree.objects.all().order_by('-id')
    serializer_class = EntreeSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            _exiger_roles(request, 'agent_dsid', 'agent_came')

    def get_queryset(self):
        qs = super().get_queryset()
        if _role(self.request.user) == 'demandeur' and not _est_admin(self.request.user):
            return qs.none()
        return qs

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    @action(detail=True, methods=['get'], url_path='document')
    def document(self, request, pk=None):
        entree = self.get_object()
        return _reponse_fichier(entree.document_fichier)

    @action(detail=True, methods=['post'], url_path='televerser-document', parser_classes=[MultiPartParser, FormParser])
    def televerser_document(self, request, pk=None):
        _exiger_roles(request, 'agent_came')
        entree = self.get_object()
        fichier = request.FILES.get('document_fichier')
        if not fichier:
            raise DRFValidationError({'document_fichier': 'Choisissez le document de l’entrée.'})
        verifier_document(fichier)
        entree.document_fichier = fichier
        entree.save(update_fields=['document_fichier'])
        return Response(EntreeSerializer(entree, context={'request': request}).data)

    @action(detail=True, methods=['post'], serializer_class=LigneEntreeInputSerializer)
    @gerer_erreurs_metier
    def ajouter_ligne(self, request, pk=None):
        entree = self.get_object()
        entree_data = self.get_serializer(data=request.data)
        entree_data.is_valid(raise_exception=True)
        type_article = entree_data.validated_data['type_article']
        quantite = entree_data.validated_data['quantite']

        ligne, articles = services.enregistrer_ligne_entree(
            entree=entree,
            type_article=type_article,
            quantite=quantite,
            utilisateur=request.user,
            nom_agent=request.session.get('agent_nom_saisi', ''),
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

class BonSortieViewSet(ExporterMixin, SuppressionProtegeeMixin, viewsets.ModelViewSet):
    queryset = BonSortie.objects.all().order_by('-id')
    serializer_class = BonSortieSerializer
    permission_classes = [IsAuthenticated]

    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = _role(user)
        if role == 'demandeur' and not _est_admin(user):
            entite_ids = list(user.entites.values_list('id', flat=True))
            if len(entite_ids) != 1:
                return qs.none()
            qs = qs.filter(entite_id=entite_ids[0], utilisateur=user)
        elif role == 'agent_came' and not _est_admin(user):
            qs = qs.filter(statut__in=['valide', 'sorti'])
        qs = _filtrer(qs, self.request, ['statut', 'entite'])
        return qs

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            _exiger_roles(request, 'demandeur', 'agent_direction')

    def perform_create(self, serializer):
        user = self.request.user
        if _role(user) == 'demandeur' and not _est_admin(user):
            ids = list(user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                raise DRFValidationError({'entite': 'Le compte demandeur doit être associé à exactement une entité par l’administrateur.'})
            serializer.save(utilisateur=user, entite_id=ids[0])
        else:
            serializer.save(utilisateur=user)

    def perform_update(self, serializer):
        if not _est_admin(self.request.user) and serializer.instance.utilisateur_id != self.request.user.id:
            raise DRFValidationError('Vous ne pouvez modifier que vos propres bons.')
        if serializer.instance.statut != 'brouillon':
            raise DRFValidationError("Un bon de sortie soumis ne peut plus être modifié.")
        if _role(self.request.user) == 'demandeur' and not _est_admin(self.request.user):
            ids = list(self.request.user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                raise DRFValidationError({'entite': 'Compte demandeur sans entité unique.'})
            serializer.save(entite_id=ids[0])
        else:
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

    @action(detail=True, methods=['get'], url_path='document')
    def document(self, request, pk=None):
        bs = self.get_object()
        return _reponse_fichier(bs.document_fichier)

    @action(detail=True, methods=['post'], url_path='televerser-document', parser_classes=[MultiPartParser, FormParser])
    def televerser_document(self, request, pk=None):
        bs = self.get_object()
        if not _est_admin(request.user) and (bs.utilisateur_id != request.user.id or _role(request.user) not in ('demandeur', 'agent_direction')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Seul le demandeur créateur peut déposer le justificatif du bon.')
        fichier = request.FILES.get('document_fichier')
        if not fichier:
            raise DRFValidationError({'document_fichier': 'Choisissez un fichier.'})
        verifier_document(fichier)
        bs.document_fichier = fichier
        bs.save(update_fields=['document_fichier'])
        return Response(BonSortieSerializer(bs, context={'request': request}).data)

    @action(detail=True, methods=['post'], serializer_class=BonSortieSerializer)
    @gerer_erreurs_metier
    def soumettre(self, request, pk=None):
        """BROUILLON -> EN_ATTENTE_AUTORISATION (aucun corps de requête nécessaire)."""
        bon_sortie = services.soumettre_bon_sortie(self.get_object(), request.user)
        return Response(BonSortieSerializer(bon_sortie).data)


class LigneBSortieViewSet(ExporterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Lignes de demande. Filtres : ?bon_sortie=, ?etat_ligne=, ?type_article=.
    Le DCA ne traite que ?etat_ligne=autorisee ; une ligne refusée par le DSID ne lui est jamais proposée.
    """
    queryset = LigneBSortie.objects.select_related('bon_sortie', 'type_article').order_by('id')
    serializer_class = LigneBSortieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _role(user) == 'demandeur' and not _est_admin(user):
            ids = list(user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                return qs.none()
            qs = qs.filter(bon_sortie__entite_id=ids[0], bon_sortie__utilisateur=user)
        elif _role(user) == 'agent_came' and not _est_admin(user):
            qs = qs.filter(bon_sortie__statut__in=['valide', 'sorti'])
        return _filtrer(qs, self.request, ['bon_sortie', 'etat_ligne', 'type_article'])

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


class IntervientViewSet(ExporterMixin, viewsets.ReadOnlyModelViewSet):
    """Historique des décisions (autorisations / validations), jamais supprimé ni modifié."""
    queryset = Intervient.objects.all().order_by('-date_intervention')
    serializer_class = IntervientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _role(user) == 'demandeur' and not _est_admin(user):
            ids = list(user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                return qs.none()
            qs = qs.filter(ligne_bsortie__bon_sortie__entite_id=ids[0], ligne_bsortie__bon_sortie__utilisateur=user)
        return _filtrer(qs, self.request, ['ligne_bsortie', 'role_intervention'])


# ----- Sorties -----

class SortieViewSet(ExporterMixin, viewsets.ReadOnlyModelViewSet):
    # Lecture seule : une Sortie ne se crée que par /sorties/effectuer/ (BS validé uniquement).
    queryset = Sortie.objects.all().order_by('-id')
    serializer_class = SortieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _role(user) == 'demandeur' and not _est_admin(user):
            ids = list(user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                return qs.none()
            qs = qs.filter(bon_sortie__entite_id=ids[0], bon_sortie__utilisateur=user)
        return qs

    @action(detail=False, methods=['post'], serializer_class=SortieInputSerializer, parser_classes=[MultiPartParser, FormParser])
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
            bon_sortie,
            donnees.validated_data['date_sortie'],
            request.user,
            livraisons,
            nom_agent=request.session.get('agent_nom_saisi', ''),
            document_livraison=donnees.validated_data['document_livraison'],
        )
        return Response(SortieSerializer(sortie).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='preuve')
    def preuve(self, request, pk=None):
        sortie = self.get_object()
        return _reponse_fichier(sortie.document_livraison)

    @action(detail=True, methods=['post'], url_path='televerser-preuve', parser_classes=[MultiPartParser, FormParser])
    def televerser_preuve(self, request, pk=None):
        _exiger_roles(request, 'agent_came')
        sortie = self.get_object()
        fichier = request.FILES.get('document_livraison')
        if not fichier:
            raise DRFValidationError({'document_livraison': 'Choisissez le justificatif de livraison.'})
        verifier_document(fichier)
        sortie.document_livraison = fichier
        sortie.save(update_fields=['document_livraison'])
        return Response(SortieSerializer(sortie, context={'request': request}).data)


class MouvementViewSet(ExporterMixin, viewsets.ReadOnlyModelViewSet):
    # Lecture seule : un Mouvement est toujours la conséquence d'une opération (entrée, sortie...).
    queryset = Mouvement.objects.all().order_by('-date_mouvement', '-id')
    serializer_class = MouvementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _role(user) == 'demandeur' and not _est_admin(user):
            ids = list(user.entites.values_list('id', flat=True))
            if len(ids) != 1:
                return qs.none()
            qs = qs.filter(entite_id=ids[0])
        return _filtrer(qs, self.request, ['type_mouvement', 'article', 'type_article', 'entite'])



class UtilisateurViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Utilisateur.objects.all().prefetch_related('entites')
    serializer_class = UtilisateurProfileSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        _exiger_roles(request, 'admin')

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreationSerializer

        return UtilisateurProfileSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        donnees = serializer.validated_data

        if donnees.get('role') == 'demandeur':
            entites = donnees.get('entites', [])

            if len(entites) != 1:
                raise DRFValidationError({
                    'entites': 'Un compte Demandeur doit avoir exactement une entité.'
                })

            entite = Entite.objects.select_for_update().get(
                pk=entites[0].pk
            )

            compte_existant = Utilisateur.objects.filter(
                role='demandeur',
                entites=entite
            ).exists()

            if compte_existant:
                raise DRFValidationError({
                    'entites': 'Un compte Demandeur existe déjà pour cette entité.'
                })

        serializer.save()