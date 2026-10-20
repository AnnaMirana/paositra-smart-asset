from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from . import auth_api

router = DefaultRouter()
router.register('categories', views.CategorieViewSet)
router.register('fournisseurs', views.FournisseurViewSet)
router.register('entites', views.EntiteViewSet)
router.register('types-article', views.TypeArticleViewSet)
router.register('articles', views.ArticleViewSet)
router.register('entrees', views.EntreeViewSet)
router.register('bons-sortie', views.BonSortieViewSet)
router.register('lignes-bsortie', views.LigneBSortieViewSet)
router.register('interventions', views.IntervientViewSet)
router.register('sorties', views.SortieViewSet)
router.register('mouvements', views.MouvementViewSet)

urlpatterns = [
    path('auth/me/', auth_api.me),
    path('auth/login/', auth_api.login_view),
    path('auth/logout/', auth_api.logout_view),
    path('', include(router.urls)),
]
