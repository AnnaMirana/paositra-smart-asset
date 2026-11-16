
"""
Tests de l'authentification PAOSITRA SMART ASSET.

Vérifie :
- Connexion avec prénom + nom et mot de passe.
- Refus des mauvais identifiants.
- Refus des comptes désactivés.
- Gestion des sessions et déconnexion.
- Protection CSRF.
- Affichage des noms dans les réponses API.
- Blocage et changement obligatoire du mot de passe temporaire.

Lancer avec :
python manage.py test inventaire.test_auth
"""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from . import services
from .models import (
    BonSortie,
    Categorie,
    Entite,
    Entree,
    Fournisseur,
    LigneBSortie,
    Mouvement,
    TypeArticle,
    Utilisateur,
)


class AuthReactTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username='agent.dsid',
            first_name='Agent',
            last_name='DSID',
            password='secret123',
            role='agent_dsid',
        )

        self.admin = Utilisateur.objects.create_superuser(
            username='administrateur',
            email='admin@test.mg',
            password='secret123',
        )

        self.admin.first_name = 'Administrateur'
        self.admin.last_name = 'Test'
        self.admin.save()

    def connexion(self, client=None, nom='Agent DSID'):
        if client is None:
            client = APIClient()

        return client.post(
            '/api/auth/login/',
            {
                'nom': nom,
                'password': 'secret123',
            },
            format='json',
        )

    def test_me_anonyme(self):
        client = APIClient()

        response = client.get('/api/auth/me/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {'authentifie': False}
        )
        self.assertIn(
            'csrftoken',
            response.cookies,
            'Le cookie CSRF doit être posé pour React.'
        )

    def test_login_avec_nom_et_mot_de_passe(self):
        client = APIClient()

        response = self.connexion(client)

        self.assertEqual(
            response.status_code,
            200,
            response.content
        )

        self.assertTrue(response.data['authentifie'])
        self.assertEqual(response.data['role'], 'agent_dsid')
        self.assertEqual(
            response.data['nom_complet'],
            'Agent DSID'
        )

        self.assertEqual(
            client.get('/api/auth/me/').data['role'],
            'agent_dsid'
        )

    def test_login_ne_demande_pas_username_ni_nom_agent(self):
        client = APIClient()

        response = client.post(
            '/api/auth/login/',
            {
                'nom': 'Agent DSID',
                'password': 'secret123',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
            response.content
        )

    def test_login_mauvais_mot_de_passe(self):
        response = APIClient().post(
            '/api/auth/login/',
            {
                'nom': 'Agent DSID',
                'password': 'faux',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('erreur', response.data)

    def test_login_nom_incorrect(self):
        response = APIClient().post(
            '/api/auth/login/',
            {
                'nom': 'Nom Inconnu',
                'password': 'secret123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_login_compte_desactive_refuse(self):
        self.user.actif = False
        self.user.save()

        response = APIClient().post(
            '/api/auth/login/',
            {
                'nom': 'Agent DSID',
                'password': 'secret123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_logout_ferme_la_session(self):
        client = APIClient()

        response = self.connexion(client)
        self.assertEqual(response.status_code, 200)

        response = client.post('/api/auth/logout/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            client.get('/api/types-article/').status_code,
            403
        )

        self.assertEqual(
            client.get('/api/auth/me/').data,
            {'authentifie': False}
        )

    def test_logout_sans_connexion_refuse(self):
        response = APIClient().post('/api/auth/logout/')

        self.assertIn(
            response.status_code,
            [200, 401, 403]
        )

    def test_csrf_reellement_exige_pour_les_ecritures(self):
        client = APIClient(enforce_csrf_checks=True)

        client.get('/api/auth/me/')

        response = client.post(
            '/api/auth/login/',
            {
                'nom': 'Administrateur Test',
                'password': 'secret123',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
            response.content
        )

        token = client.cookies['csrftoken'].value

        categorie = {
            'nom_categorie': 'Test CSRF'
        }

        response = client.post(
            '/api/categories/',
            categorie,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            403,
            'Une écriture sans en-tête CSRF doit être refusée.'
        )

        response = client.post(
            '/api/categories/',
            categorie,
            format='json',
            HTTP_X_CSRFTOKEN=token
        )

        self.assertEqual(
            response.status_code,
            201,
            response.content
        )

        response = client.post(
            '/api/auth/logout/',
            format='json',
            HTTP_X_CSRFTOKEN=token
        )

        self.assertEqual(response.status_code, 200)


class ChampsAffichageTests(TestCase):
    """
    Vérifie que les API renvoient les noms des utilisateurs,
    des entités et des articles.
    """

    def setUp(self):
        self.dem = Utilisateur.objects.create_user(
            username='demandeur',
            first_name='Jean',
            last_name='Demandeur',
            password='x',
            role='demandeur'
        )

        self.root = Utilisateur.objects.create_superuser(
            username='root',
            email='r@t.mg',
            password='x'
        )

        self.cat = Categorie.objects.create(
            nom_categorie='Consommable'
        )

        self.f = Fournisseur.objects.create(
            nom_fournisseur='Fournisseur Test'
        )

        self.entite = Entite.objects.create(
            nom_entite='Agence Tsaralalana',
            sigle_entite='10102',
            type_entite='agence'
        )

        self.t_encre = TypeArticle.objects.create(
            nom_type_article='Cartouche',
            categorie=self.cat
        )

        self.t_pc = TypeArticle.objects.create(
            nom_type_article='Portable',
            categorie=self.cat,
            gestion_individuelle=True
        )

        self.c = APIClient()
        self.c.force_authenticate(self.root)

    def test_noms_dans_entree_bon_et_mouvements(self):
        entree = Entree.objects.create(
            date_entree=date.today(),
            ref_entree='E1',
            origine='achat',
            fournisseur=self.f,
            utilisateur=self.root
        )

        services.enregistrer_ligne_entree(
            entree,
            self.t_encre,
            10,
            self.root
        )

        services.enregistrer_ligne_entree(
            entree,
            self.t_pc,
            1,
            self.root
        )

        bon = BonSortie.objects.create(
            reference_bs='BS1',
            date_bs=date.today(),
            entite=self.entite,
            utilisateur=self.dem
        )

        LigneBSortie.objects.create(
            bon_sortie=bon,
            type_article=self.t_encre,
            quantite_demandee=3
        )

        self.assertEqual(
            self.c.get(
                f'/api/entrees/{entree.id}/'
            ).data['utilisateur_nom'],
            'root'
        )

        self.assertEqual(
            self.c.get(
                f'/api/bons-sortie/{bon.id}/'
            ).data['utilisateur_nom'],
            'Jean Demandeur'
        )

        mouvements = self.c.get(
            '/api/mouvements/'
        ).data

        mouvements = (
            mouvements['results']
            if isinstance(mouvements, dict)
            else mouvements
        )

        par_type = [
            mouvement
            for mouvement in mouvements
            if mouvement['type_article']
        ]

        par_article = [
            mouvement
            for mouvement in mouvements
            if mouvement['article']
        ]

        self.assertEqual(len(par_type), 1)

        self.assertEqual(
            (
                par_type[0]['type_article_nom'],
                par_type[0]['utilisateur_nom']
            ),
            ('Cartouche', 'root')
        )
        self.assertIsNone(par_type[0]['entite_nom'])

        self.assertEqual(len(par_article), 1)
        self.assertIsNone(par_article[0]['type_article_nom'])

    def test_mouvement_de_sortie_porte_le_nom_de_l_entite(self):
        Mouvement.objects.create(
            type_mouvement='sortie',
            type_article=self.t_encre,
            quantite=2,
            utilisateur=self.root,
            entite=self.entite
        )

        response = self.c.get(
            '/api/mouvements/?type_mouvement=sortie'
        )

        mouvements = (
            response.data['results']
            if isinstance(response.data, dict)
            else response.data
        )

        self.assertEqual(
            mouvements[0]['entite_nom'],
            'Agence Tsaralalana'
        )


class PremiereConnexionTests(TestCase):

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username='nouveau.compte',
            first_name='Nouveau',
            last_name='Compte',
            email='nouveau@test.mg',
            password='Temporaire!12345',
            role='agent_dsid',
        )

        self.user.doit_changer_mot_de_passe = True

        self.user.mot_de_passe_temporaire_expire_le = (
            timezone.now() + timedelta(hours=24)
        )

        self.user.save()

        self.client_api = APIClient()

    def test_premiere_connexion_bloque_les_fonctionnalites(self):
        response = self.client_api.post(
            '/api/auth/login/',
            {
                'nom': 'Nouveau Compte',
                'password': 'Temporaire!12345',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
            response.content
        )

        self.assertTrue(
            response.data['doit_changer_mot_de_passe']
        )

        self.assertEqual(
            self.client_api.get('/api/types-article/').status_code,
            403
        )

    def test_changement_mot_de_passe_debloque_le_compte(self):
        self.client_api.post(
            '/api/auth/login/',
            {
                'nom': 'Nouveau Compte',
                'password': 'Temporaire!12345',
            },
            format='json',
        )

        response = self.client_api.post(
            '/api/auth/changer-mot-de-passe/',
            {
                'ancien_mot_de_passe': 'Temporaire!12345',
                'nouveau_mot_de_passe': 'NouveauTresSolide!2026',
                'confirmation': 'NouveauTresSolide!2026',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
            response.content
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.doit_changer_mot_de_passe
        )

        self.assertTrue(
            self.user.check_password('NouveauTresSolide!2026')
        )

        self.assertEqual(
            self.client_api.get('/api/types-article/').status_code,
            200
        )

    def test_mot_de_passe_temporaire_expire_refuse(self):
        self.user.mot_de_passe_temporaire_expire_le = (
            timezone.now() - timedelta(hours=1)
        )
        self.user.save()

        response = self.client_api.post(
            '/api/auth/login/',
            {
                'nom': 'Nouveau Compte',
                'password': 'Temporaire!12345',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('erreur', response.data)
