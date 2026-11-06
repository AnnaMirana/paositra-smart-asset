from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import services
from .models import (
    Article, BonSortie, Categorie, Entite, Entree, Fournisseur, Intervient,
    LigneBSortie, LigneEntree, LigneSortie, Mouvement, Sortie, TypeArticle,
    Utilisateur,
)


class LectureSeuleAdmin(admin.ModelAdmin):
    """
    Historique : ces données sont créées uniquement par la logique métier
    (services.py), jamais à la main — sinon on contournerait les règles de stock
    et de workflow.
    """
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'role', 'actif', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Paositra', {'fields': ('role', 'actif', 'entites')}),
    )


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_categorie')
    search_fields = ('nom_categorie',)


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_fournisseur')
    search_fields = ('nom_fournisseur',)


@admin.register(Entite)
class EntiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_entite', 'sigle_entite', 'type_entite')
    list_filter = ('type_entite',)
    search_fields = ('nom_entite', 'sigle_entite')


@admin.register(TypeArticle)
class TypeArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_type_article', 'marque', 'categorie', 'gestion_individuelle', 'quantite_stock')
    list_filter = ('gestion_individuelle', 'categorie')
    search_fields = ('nom_type_article', 'marque')
    # Le stock n'est jamais saisi à la main : il est maintenu par services.py.
    readonly_fields = ('quantite_stock',)


class LigneEntreeInline(admin.TabularInline):
    model = LigneEntree
    extra = 1

    # Une ligne enregistrée a déjà créé stock/articles/mouvements : on ne la
    # modifie ni ne la supprime ici (jamais de suppression, correction tracée).
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Entree)
class EntreeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ref_entree', 'date_entree', 'origine', 'fournisseur', 'utilisateur')
    list_filter = ('origine',)
    readonly_fields = ('utilisateur',)
    inlines = [LigneEntreeInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.utilisateur = request.user  # compte connecté = auteur de l'opération
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Une nouvelle LigneEntree passe par services.enregistrer_ligne_entree
        (création des Article / Mouvement, mise à jour du stock) — exactement
        comme l'API ; l'enregistrement direct par l'admin contournerait la règle.
        """
        if formset.model != LigneEntree:
            return super().save_formset(request, form, formset, change)
        for obj in formset.save(commit=False):
            if obj.pk is None:
                services.enregistrer_ligne_entree(
                    entree=obj.entree, type_article=obj.type_article,
                    quantite=obj.quantite, utilisateur=request.user,
                )
        formset.save_m2m()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'ref_article', 'type_article', 'num_serie', 'qr_code')
    list_filter = ('type_article',)
    search_fields = ('ref_article', 'num_serie', 'qr_code')
    # Les articles sont créés par l'entrée ; ici on complète ref / n° de série / QR.
    readonly_fields = ('type_article', 'ligne_entree')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LigneBSortieInline(admin.TabularInline):
    model = LigneBSortie
    extra = 1
    fields = ('type_article', 'quantite_demandee', 'quantite_autorisee', 'quantite_validee', 'etat_ligne')
    readonly_fields = ('quantite_autorisee', 'quantite_validee', 'etat_ligne')  # gérés par le workflow

    def _brouillon(self, obj):
        return obj is None or obj.statut == 'brouillon'

    def has_add_permission(self, request, obj=None):
        return self._brouillon(obj)

    def has_change_permission(self, request, obj=None):
        return self._brouillon(obj)

    def has_delete_permission(self, request, obj=None):
        return self._brouillon(obj)


@admin.register(BonSortie)
class BonSortieAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference_bs', 'entite', 'statut', 'date_bs', 'utilisateur')
    list_filter = ('statut', 'entite')
    search_fields = ('reference_bs',)
    inlines = [LigneBSortieInline]

    def get_readonly_fields(self, request, obj=None):
        champs = ['statut', 'utilisateur']  # statut : géré par le workflow ; utilisateur : compte connecté
        if obj is not None and obj.statut != 'brouillon':
            champs += ['reference_bs', 'document', 'date_bs', 'entite']
        return champs

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.statut == 'brouillon'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.utilisateur = request.user
        super().save_model(request, obj, form, change)


@admin.register(LigneBSortie)
class LigneBSortieAdmin(LectureSeuleAdmin):
    list_display = ('id', 'bon_sortie', 'type_article', 'quantite_demandee', 'quantite_autorisee',
                    'quantite_validee', 'etat_ligne')
    list_filter = ('etat_ligne',)


@admin.register(Intervient)
class IntervientAdmin(LectureSeuleAdmin):
    list_display = ('id', 'ligne_bsortie', 'role_intervention', 'utilisateur', 'quantite_decidee',
                    'date_intervention', 'motif')
    list_filter = ('role_intervention',)


@admin.register(Sortie)
class SortieAdmin(LectureSeuleAdmin):
    list_display = ('id', 'ref_sortie', 'bon_sortie', 'date_sortie', 'quantite')


@admin.register(LigneSortie)
class LigneSortieAdmin(LectureSeuleAdmin):
    list_display = ('id', 'sortie', 'ligne_bsortie', 'type_article', 'quantite_livree')


@admin.register(Mouvement)
class MouvementAdmin(LectureSeuleAdmin):
    list_display = ('id', 'type_mouvement', 'article', 'type_article', 'quantite', 'utilisateur',
                    'entite', 'date_mouvement')
    list_filter = ('type_mouvement', 'entite')
