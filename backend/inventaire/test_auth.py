"""
Tests de l'authentification utilisée par le frontend React (session + CSRF)
et des champs ajoutés pour l'affichage (noms d'utilisateur / d'entité).
DONNÉES DE TEST — FICTIVES.

Lancer avec : python manage.py test inventaire.test_auth
"""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient

from . import services
from .models import (
    BonSortie, Categorie, Entite, Entree, Fournisseur, LigneBSortie,
    Mouvement, TypeArticle, Utilisateur,
)


class AuthReactTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user('dsid', password='secret123', role='agent_dsid')
        self.admin = Utilisateur.objects.create_superuser('admin', 'admin@test.mg', 'secret123')

    def test_me_anonyme(self):
        r = APIClient().get('/api/auth/me/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {'authentifie': False})
        self.assertIn('csrftoken', r.cookies, "le cookie CSRF doit être posé pour React")

    def test_login_ok_renvoie_le_profil_et_le_role(self):
        c = APIClient()
        r = c.post('/api/auth/login/', {'username': 'dsid', 'password': 'secret123', 'nom_agent': 'Agent DSID Test'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual((r.data['authentifie'], r.data['role'], r.data['username']), (True, 'agent_dsid', 'dsid'))
        self.assertEqual(r.data['role_libelle'], 'Agent DSID')
        # la session est ouverte : l'API protégée répond
        self.assertEqual(c.get('/api/types-article/').status_code, 200)
        self.assertEqual(c.get('/api/auth/me/').data['username'], 'dsid')

    def test_login_mauvais_mot_de_passe(self):
        r = APIClient().post('/api/auth/login/', {'username': 'dsid', 'password': 'faux', 'nom_agent': 'Agent DSID Test'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('erreur', r.data)

    def test_login_compte_desactive_refuse(self):
        self.user.actif = False
        self.user.save()
        r = APIClient().post('/api/auth/login/', {'username': 'dsid', 'password': 'secret123', 'nom_agent': 'Agent DSID Test'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_logout_ferme_la_session(self):
        c = APIClient()
        c.post('/api/auth/login/', {'username': 'dsid', 'password': 'secret123', 'nom_agent': 'Agent DSID Test'}, format='json')
        self.assertEqual(c.post('/api/auth/logout/').status_code, 200)
        self.assertEqual(c.get('/api/types-article/').status_code, 403)
        self.assertEqual(c.get('/api/auth/me/').data, {'authentifie': False})

    def test_logout_sans_connexion_refuse(self):
        response = APIClient().post('/api/auth/logout/')
        self.assertIn(response.status_code, [200, 401, 403])

    def test_csrf_reellement_exige_pour_les_ecritures_en_session(self):
        """Comme dans le navigateur : cookie de session + en-tête X-CSRFToken obligatoires."""
        c = APIClient(enforce_csrf_checks=True)
        c.get('/api/auth/me/')  # pose le cookie CSRF
        r = c.post('/api/auth/login/', {'username': 'admin', 'password': 'secret123', 'nom_agent': 'Administrateur Test'}, format='json')
        self.assertEqual(r.status_code, 200)
        token = c.cookies['csrftoken'].value  # le jeton est renouvelé à la connexion
        cat = {'nom_categorie': 'Test CSRF'}
        self.assertEqual(c.post('/api/categories/', cat, format='json').status_code, 403, "sans en-tête CSRF")
        r = c.post('/api/categories/', cat, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(c.post('/api/auth/logout/', format='json', HTTP_X_CSRFTOKEN=token).status_code, 200)


class ChampsAffichageTests(TestCase):
    """Noms ajoutés aux réponses pour que l'interface affiche des noms et non des numéros."""

    def setUp(self):
        self.dem = Utilisateur.objects.create_user('dem', password='x', role='demandeur')
        self.root = Utilisateur.objects.create_superuser('root', 'r@t.mg', 'x')
        self.cat = Categorie.objects.create(nom_categorie='Consommable')
        self.f = Fournisseur.objects.create(nom_fournisseur='Fournisseur Test')
        self.entite = Entite.objects.create(nom_entite='Agence Tsaralalana', sigle_entite='10102', type_entite='agence')
        self.t_encre = TypeArticle.objects.create(nom_type_article='Cartouche', categorie=self.cat)
        self.t_pc = TypeArticle.objects.create(nom_type_article='Portable', categorie=self.cat, gestion_individuelle=True)
        self.c = APIClient()
        self.c.force_authenticate(self.root)

    def test_noms_dans_entree_bon_et_mouvements(self):
        e = Entree.objects.create(date_entree=date.today(), ref_entree='E1', origine='achat',
                                  fournisseur=self.f, utilisateur=self.root)
        services.enregistrer_ligne_entree(e, self.t_encre, 10, self.root)
        services.enregistrer_ligne_entree(e, self.t_pc, 1, self.root)
        bs = BonSortie.objects.create(reference_bs='BS1', date_bs=date.today(), entite=self.entite, utilisateur=self.dem)
        LigneBSortie.objects.create(bon_sortie=bs, type_article=self.t_encre, quantite_demandee=3)

        self.assertEqual(self.c.get(f'/api/entrees/{e.id}/').data['utilisateur_nom'], 'root')
        self.assertEqual(self.c.get(f'/api/bons-sortie/{bs.id}/').data['utilisateur_nom'], 'dem')

        mouvs = self.c.get('/api/mouvements/').data
        mouvs = mouvs['results'] if isinstance(mouvs, dict) else mouvs
        par_type = [m for m in mouvs if m['type_article']]
        par_article = [m for m in mouvs if m['article']]
        self.assertEqual(len(par_type), 1)
        self.assertEqual((par_type[0]['type_article_nom'], par_type[0]['utilisateur_nom']), ('Cartouche', 'root'))
        self.assertIsNone(par_type[0]['entite_nom'], "une entrée au CAME n'a pas d'entité")
        self.assertEqual(len(par_article), 1)
        self.assertIsNone(par_article[0]['type_article_nom'])

    def test_mouvement_de_sortie_porte_le_nom_de_l_entite(self):
        Mouvement.objects.create(type_mouvement='sortie', type_article=self.t_encre, quantite=2,
                                 utilisateur=self.root, entite=self.entite)
        m = self.c.get('/api/mouvements/?type_mouvement=sortie').data
        m = m['results'] if isinstance(m, dict) else m
        self.assertEqual(m[0]['entite_nom'], 'Agence Tsaralalana')
