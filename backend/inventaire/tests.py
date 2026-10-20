"""
Tests PAOSITRA SMART ASSET — Mois 1 (adaptés) + Mois 2 (workflow par ligne, réservation).
DONNÉES DE TEST — FICTIVES.

Lancer avec : python manage.py test inventaire
"""
from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from . import services
from .models import (
    Article, BonSortie, Categorie, Entite, Entree, Fournisseur, Intervient,
    LigneBSortie, LigneSortie, Mouvement, Sortie, TypeArticle, Utilisateur,
)


class BaseTest(TestCase):
    def setUp(self):
        mk = Utilisateur.objects.create_user
        self.root = Utilisateur.objects.create_superuser('root', 'r@test.mg', 'x')
        self.demandeur = mk('dem', password='x', role='demandeur')
        self.dsid = mk('dsid', password='x', role='agent_dsid')
        self.dca = mk('dca', password='x', role='agent_validation')
        self.came = mk('came', password='x', role='agent_came')
        self.user = self.dsid  # utilisateur "neutre" pour les entrées

        self.categorie = Categorie.objects.create(nom_categorie='Informatique')
        self.fournisseur = Fournisseur.objects.create(nom_fournisseur='Fournisseur Test')
        self.entite = Entite.objects.create(nom_entite='Direction Test', sigle_entite='DT', type_entite='direction')
        self.type_ordi = TypeArticle.objects.create(
            nom_type_article='Ordinateur portable', categorie=self.categorie,
            gestion_individuelle=True, marque='HP',
        )
        self.type_encre = TypeArticle.objects.create(
            nom_type_article='Cartouche encre', categorie=self.categorie, gestion_individuelle=False,
        )
        self._n = 0

    # --- fabriques ---
    def _entree(self, ref=None):
        self._n += 1
        return Entree.objects.create(
            date_entree=date.today(), ref_entree=ref or f'E{self._n}', origine='achat',
            fournisseur=self.fournisseur, utilisateur=self.user,
        )

    def _entrer(self, type_article, quantite):
        return services.enregistrer_ligne_entree(self._entree(), type_article, quantite, self.user)

    def _bs(self, lignes, soumettre=False):
        """lignes : liste de (type_article, quantite_demandee)."""
        self._n += 1
        bs = BonSortie.objects.create(
            reference_bs=f'BS{self._n}', date_bs=date.today(), entite=self.entite, utilisateur=self.demandeur,
        )
        for t, q in lignes:
            LigneBSortie.objects.create(bon_sortie=bs, type_article=t, quantite_demandee=q)
        if soumettre:
            services.soumettre_bon_sortie(bs, self.demandeur)
            bs.refresh_from_db()
        return bs

    def _valide(self, lignes):
        """Parcours complet : soumission, autorisation DSID, validation DCA (quantités = demandes)."""
        bs = self._bs(lignes, soumettre=True)
        for l in bs.lignes.all():
            services.autoriser_ligne(l, self.dsid, l.quantite_demandee)
        for l in bs.lignes.all():
            services.valider_ligne(l, self.dca, l.quantite_demandee)
        bs.refresh_from_db()
        return bs

    def _sortir(self, bs, livraisons=None):
        return services.effectuer_sortie(bs, date.today(), self.came, livraisons)


# =====================================================================
# SOCLE MOIS 1 (adapté au nouveau modèle et au workflow)
# =====================================================================
class SocleMois1Tests(BaseTest):

    def test_01_entree_individualisee_cree_articles(self):
        _, articles = self._entrer(self.type_ordi, 3)
        self.assertEqual(len(articles), 3)
        self.assertEqual(Article.objects.filter(type_article=self.type_ordi).count(), 3)

    def test_02_entree_consommable_ne_cree_pas_articles(self):
        _, articles = self._entrer(self.type_encre, 50)
        self.assertEqual(len(articles), 0)
        self.assertEqual(Article.objects.filter(type_article=self.type_encre).count(), 0)

    def test_03_stock_global_individualise(self):
        self._entrer(self.type_ordi, 3)
        self.type_ordi.refresh_from_db()
        self.assertEqual(self.type_ordi.quantite_stock, 3)
        self._entrer(self.type_ordi, 3)
        self.type_ordi.refresh_from_db()
        self.assertEqual(self.type_ordi.quantite_stock, 6)

    def test_04_stock_consommable(self):
        self._entrer(self.type_encre, 50)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 50)

    def test_05_sortie_individualisee_via_workflow(self):
        self._entrer(self.type_ordi, 5)
        sortie = self._sortir(self._valide([(self.type_ordi, 2)]))
        self.type_ordi.refresh_from_db()
        self.assertEqual(self.type_ordi.quantite_stock, 3, "5 entrés - 2 sortis = 3")
        self.assertEqual(sortie.articles.count(), 2)
        self.assertEqual(Mouvement.objects.filter(type_mouvement='sortie', article__in=sortie.articles.all()).count(), 2)

    def test_06_sortie_consommable_via_workflow(self):
        self._entrer(self.type_encre, 50)
        self._sortir(self._valide([(self.type_encre, 5)]))
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 45)

    def test_07_stock_insuffisant_bloque_a_l_autorisation(self):
        self._entrer(self.type_encre, 10)
        bs = self._bs([(self.type_encre, 999)], soumettre=True)
        ligne = bs.lignes.get()
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(ligne, self.dsid, 999)
        ligne.refresh_from_db()
        self.assertEqual(ligne.etat_ligne, 'demandee', "la ligne ne doit pas avoir bougé")
        self.assertEqual(Intervient.objects.count(), 0, "aucune décision ne doit être enregistrée")
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 10)

    def test_07bis_stock_insuffisant_individualise(self):
        self._entrer(self.type_ordi, 2)
        bs = self._bs([(self.type_ordi, 5)], soumettre=True)
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(bs.lignes.get(), self.dsid, 5)
        self.type_ordi.refresh_from_db()
        self.assertEqual(self.type_ordi.quantite_stock, 2)

    def test_08_double_sortie_d_un_meme_article_impossible(self):
        self._entrer(self.type_ordi, 2)
        self._sortir(self._valide([(self.type_ordi, 2)]))
        # On simule un stock incohérent qui annoncerait encore 2 disponibles :
        self.type_ordi.refresh_from_db()
        self.type_ordi.quantite_stock = 2
        self.type_ordi.save(update_fields=['quantite_stock'])
        bs2 = self._valide([(self.type_ordi, 2)])
        with self.assertRaises(ValidationError):
            self._sortir(bs2)
        self.assertEqual(Article.objects.filter(sorties__isnull=False).distinct().count(), 2)
        bs2.refresh_from_db()
        self.assertEqual(bs2.statut, 'valide', "le BS reste validé, rien n'a été écrit")

    def test_09_mouvements_crees_correctement(self):
        _, articles = self._entrer(self.type_ordi, 1)
        mvt = Mouvement.objects.get(article=articles[0])
        self.assertEqual(mvt.type_mouvement, 'entree')
        self.assertEqual(mvt.utilisateur, self.user)
        self.assertIsNone(mvt.type_article)
        self.assertIsNone(mvt.quantite)
        self._entrer(self.type_encre, 20)
        mvt2 = Mouvement.objects.get(type_article=self.type_encre, type_mouvement='entree')
        self.assertEqual(mvt2.quantite, 20)
        self.assertIsNone(mvt2.article)

    def test_10_utilisateur_enregistre_et_synchronise(self):
        entree = self._entree()
        self.assertEqual(entree.utilisateur, self.user)
        self.user.actif = False
        self.user.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_11_rollback_complet_si_erreur_en_cours_de_sortie(self):
        self._entrer(self.type_encre, 10)
        self._entrer(self.type_ordi, 3)
        bs = self._valide([(self.type_encre, 5), (self.type_ordi, 3)])
        # Les articles réels des ordinateurs sont déjà tous sortis alors que le stock les annonce encore :
        for a in Article.objects.filter(type_article=self.type_ordi):
            s = Sortie.objects.create(bon_sortie=self._bs([(self.type_ordi, 1)]), date_sortie=date.today(),
                                      quantite=1, ref_sortie=f'X{a.id}')
            s.articles.add(a)
        with self.assertRaises(ValidationError):
            self._sortir(bs)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 10, "la ligne consommable ne doit pas être sortie à moitié")
        self.assertFalse(Sortie.objects.filter(bon_sortie=bs).exists())
        self.assertFalse(Mouvement.objects.filter(type_mouvement='sortie', type_article=self.type_encre).exists())
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'valide')


# =====================================================================
# RÈGLES MOIS 2 : modèle
# =====================================================================
class ModeleMois2Tests(BaseTest):

    def test_categorie_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categorie.objects.create(nom_categorie='Informatique')

    def test_type_unique_par_categorie_mais_autorise_dans_une_autre(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            TypeArticle.objects.create(nom_type_article='Ordinateur portable', categorie=self.categorie)
        autre = Categorie.objects.create(nom_categorie='Mobilier')
        TypeArticle.objects.create(nom_type_article='Ordinateur portable', categorie=autre)  # autorisé

    def test_fournisseur_obligatoire_dans_entree(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Entree.objects.create(date_entree=date.today(), ref_entree='SANS-F', origine='don',
                                  utilisateur=self.user)

    def test_marque_sur_type_pas_sur_article(self):
        _, articles = self._entrer(self.type_ordi, 1)
        self.assertEqual(self.type_ordi.marque, 'HP')
        self.assertFalse(hasattr(articles[0], 'marque'))
        self.assertFalse(hasattr(articles[0], 'caracteristique'))

    def test_mouvement_article_xor_type_article(self):
        _, articles = self._entrer(self.type_ordi, 1)
        regles = [
            dict(article=articles[0], type_article=self.type_ordi),          # les deux
            dict(),                                                           # aucun
            dict(type_article=self.type_encre),                              # type sans quantité
            dict(article=articles[0], quantite=2),                           # article avec quantité
        ]
        for champs in regles:
            with self.assertRaises(ValidationError):
                Mouvement(type_mouvement='entree', utilisateur=self.user, **champs).clean()
        Mouvement(type_mouvement='entree', utilisateur=self.user, article=articles[0]).clean()
        Mouvement(type_mouvement='entree', utilisateur=self.user, type_article=self.type_encre, quantite=3).clean()

    def test_mouvement_peut_ne_pas_avoir_d_entite(self):
        self._entrer(self.type_encre, 5)
        self.assertIsNone(Mouvement.objects.get(type_mouvement='entree').entite)

    def test_entite_types(self):
        for t in ('direction', 'agence', 'depot'):
            Entite.objects.create(nom_entite=f'{t} x', sigle_entite='X', type_entite=t)


# =====================================================================
# WORKFLOW DU BON DE SORTIE (ligne par ligne)
# =====================================================================
class WorkflowTests(BaseTest):

    def test_soumission_exige_au_moins_une_ligne(self):
        bs = self._bs([])
        with self.assertRaises(ValidationError):
            services.soumettre_bon_sortie(bs, self.demandeur)

    def test_soumission_brouillon_vers_attente_autorisation(self):
        bs = self._bs([(self.type_encre, 3)])
        self.assertEqual(bs.statut, 'brouillon')
        services.soumettre_bon_sortie(bs, self.demandeur)
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'en_attente_autorisation')
        with self.assertRaises(ValidationError):  # déjà soumis
            services.soumettre_bon_sortie(bs, self.demandeur)

    def test_seul_le_createur_soumet(self):
        bs = self._bs([(self.type_encre, 3)])
        autre = Utilisateur.objects.create_user('dem2', password='x', role='demandeur')
        with self.assertRaises(PermissionDenied):
            services.soumettre_bon_sortie(bs, autre)

    def test_autorisation_partielle_exige_un_motif_et_est_tracee(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        ligne = bs.lignes.get()
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(ligne, self.dsid, 7)  # sans motif
        services.autoriser_ligne(ligne, self.dsid, 7, motif='stock limité')
        ligne.refresh_from_db()
        self.assertEqual((ligne.quantite_autorisee, ligne.etat_ligne), (7, 'autorisee'))
        iv = Intervient.objects.get(ligne_bsortie=ligne)
        self.assertEqual((iv.role_intervention, iv.quantite_decidee, iv.motif, iv.utilisateur),
                         ('autorisation', 7, 'stock limité', self.dsid))
        self.assertIsNotNone(iv.date_intervention)

    def test_autorisation_ne_depasse_pas_la_demande(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(bs.lignes.get(), self.dsid, 6, motif='trop')

    def test_refus_ligne_quantite_zero_avec_motif(self):
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        ligne = bs.lignes.get()
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(ligne, self.dsid, 0)  # refus sans motif
        services.autoriser_ligne(ligne, self.dsid, 0, motif='non justifié')
        ligne.refresh_from_db()
        self.assertEqual((ligne.etat_ligne, ligne.quantite_autorisee), ('refusee', 0))
        self.assertEqual(Intervient.objects.get().quantite_decidee, 0)

    def test_toutes_lignes_refusees_donne_bs_refuse(self):
        bs = self._bs([(self.type_encre, 5), (self.type_ordi, 2)], soumettre=True)
        for l in bs.lignes.all():
            services.autoriser_ligne(l, self.dsid, 0, motif='refus')
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'refuse')

    def test_lignes_refusees_ne_bloquent_pas_les_autres(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        bs = self._bs([(self.type_encre, 5), (self.type_ordi, 2)], soumettre=True)
        l_encre, l_ordi = bs.lignes.order_by('id')
        services.autoriser_ligne(l_encre, self.dsid, 0, motif='refus')
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'en_attente_autorisation', "il reste une ligne à traiter")
        services.autoriser_ligne(l_ordi, self.dsid, 2)
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'en_attente_validation')

    def test_ligne_refusee_par_dsid_pas_proposee_au_dca(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        bs = self._bs([(self.type_encre, 5), (self.type_ordi, 2)], soumettre=True)
        l_encre, l_ordi = bs.lignes.order_by('id')
        services.autoriser_ligne(l_encre, self.dsid, 0, motif='refus')
        services.autoriser_ligne(l_ordi, self.dsid, 2)
        with self.assertRaises(ValidationError):
            services.valider_ligne(l_encre, self.dca, 5)
        a_valider = list(LigneBSortie.objects.filter(bon_sortie=bs, etat_ligne='autorisee'))
        self.assertEqual(a_valider, [l_ordi])

    def test_validation_dca_modifie_quantite_avec_motif(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        ligne = bs.lignes.get()
        services.autoriser_ligne(ligne, self.dsid, 10)
        with self.assertRaises(ValidationError):
            services.valider_ligne(ligne, self.dca, 6)  # sans motif
        with self.assertRaises(ValidationError):
            services.valider_ligne(ligne, self.dca, 11, motif='plus')  # plus que l'autorisé
        services.valider_ligne(ligne, self.dca, 6, motif='budget')
        ligne.refresh_from_db()
        self.assertEqual((ligne.quantite_validee, ligne.etat_ligne), (6, 'validee'))
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'valide')
        self.assertEqual(Intervient.objects.filter(role_intervention='validation').get().quantite_decidee, 6)

    def test_dca_rejette_tout_donne_bs_refuse(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        ligne = bs.lignes.get()
        services.autoriser_ligne(ligne, self.dsid, 5)
        services.valider_ligne(ligne, self.dca, 0, motif='rejet')
        ligne.refresh_from_db()
        bs.refresh_from_db()
        self.assertEqual(ligne.etat_ligne, 'rejetee')
        self.assertEqual(bs.statut, 'refuse')

    def test_ligne_rejetee_ne_bloque_pas_la_sortie_des_autres(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        bs = self._bs([(self.type_encre, 5), (self.type_ordi, 2)], soumettre=True)
        l_encre, l_ordi = bs.lignes.order_by('id')
        services.autoriser_ligne(l_encre, self.dsid, 5)
        services.autoriser_ligne(l_ordi, self.dsid, 2)
        services.valider_ligne(l_encre, self.dca, 0, motif='rejet')
        services.valider_ligne(l_ordi, self.dca, 2)
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'valide')
        sortie = self._sortir(bs)
        self.assertEqual(sortie.quantite, 2)
        self.assertEqual(sortie.lignes.count(), 1)
        l_encre.refresh_from_db()
        self.assertEqual(l_encre.etat_ligne, 'rejetee', "reste dans l'historique")
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 20, "la ligne rejetée n'a rien sorti")

    def test_decisions_hors_etape_refusees(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 5)])  # brouillon
        ligne = bs.lignes.get()
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(ligne, self.dsid, 5)  # pas encore soumis
        services.soumettre_bon_sortie(bs, self.demandeur)
        with self.assertRaises(ValidationError):
            services.valider_ligne(ligne, self.dca, 5)  # pas encore autorisé
        services.autoriser_ligne(ligne, self.dsid, 5)
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(ligne, self.dsid, 5)  # déjà traitée

    def test_roles_respectes(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        ligne = bs.lignes.get()
        with self.assertRaises(PermissionDenied):
            services.autoriser_ligne(ligne, self.demandeur, 5)
        with self.assertRaises(PermissionDenied):
            services.autoriser_ligne(ligne, self.dca, 5)
        services.autoriser_ligne(ligne, self.dsid, 5)
        with self.assertRaises(PermissionDenied):
            services.valider_ligne(ligne, self.dsid, 5)
        services.valider_ligne(ligne, self.root, 5)  # superuser accepté
        with self.assertRaises(PermissionDenied):
            services.effectuer_sortie(bs, date.today(), self.dca)
        self._sortir(bs)

    def test_compte_desactive_ne_peut_pas_agir(self):
        self.dsid.actif = False
        self.dsid.save()
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        with self.assertRaises(PermissionDenied):
            services.autoriser_ligne(bs.lignes.get(), self.dsid, 5)


# =====================================================================
# STOCK RÉSERVÉ
# =====================================================================
class ReservationTests(BaseTest):

    def test_exemple_du_cahier_des_charges(self):
        """Stock 20 ; BS1 autorisé 10 (pas sorti) -> réservé 10, disponible 10 ; BS2 de 15 bloqué."""
        self._entrer(self.type_encre, 20)
        bs1 = self._bs([(self.type_encre, 10)], soumettre=True)
        services.autoriser_ligne(bs1.lignes.get(), self.dsid, 10)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 20, "l'autorisation ne diminue pas le stock physique")
        self.assertEqual(services.stock_reserve(self.type_encre), 10)
        self.assertEqual(services.stock_disponible_pour_autorisation(self.type_encre), 10)

        bs2 = self._bs([(self.type_encre, 15)], soumettre=True)
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(bs2.lignes.get(), self.dsid, 15)
        services.autoriser_ligne(bs2.lignes.get(), self.dsid, 10, motif='stock réservé par un autre BS')
        self.assertEqual(services.stock_disponible_pour_autorisation(self.type_encre), 0)

    def test_dca_diminue_la_quantite_la_reservation_suit(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        ligne = bs.lignes.get()
        services.autoriser_ligne(ligne, self.dsid, 10)
        self.assertEqual(services.stock_reserve(self.type_encre), 10)
        services.valider_ligne(ligne, self.dca, 6, motif='budget')
        self.assertEqual(services.stock_reserve(self.type_encre), 6, "réservation passée de 10 à 6")
        self.assertEqual(services.stock_disponible_pour_autorisation(self.type_encre), 14)

    def test_rejet_libere_la_reservation(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        ligne = bs.lignes.get()
        services.autoriser_ligne(ligne, self.dsid, 10)
        services.valider_ligne(ligne, self.dca, 0, motif='rejet')
        self.assertEqual(services.stock_reserve(self.type_encre), 0)
        self.assertEqual(services.stock_disponible_pour_autorisation(self.type_encre), 20)

    def test_refus_ne_reserve_rien(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        services.autoriser_ligne(bs.lignes.get(), self.dsid, 0, motif='refus')
        self.assertEqual(services.stock_reserve(self.type_encre), 0)

    def test_sortie_reelle_diminue_le_stock_et_libere_la_reservation(self):
        self._entrer(self.type_encre, 20)
        bs = self._valide([(self.type_encre, 10)])
        self.assertEqual(services.stock_reserve(self.type_encre), 10)
        self._sortir(bs)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 10)
        self.assertEqual(services.stock_reserve(self.type_encre), 0)
        self.assertEqual(services.stock_disponible_pour_autorisation(self.type_encre), 10)

    def test_reservation_individualise_aussi(self):
        self._entrer(self.type_ordi, 5)
        bs1 = self._bs([(self.type_ordi, 4)], soumettre=True)
        services.autoriser_ligne(bs1.lignes.get(), self.dsid, 4)
        bs2 = self._bs([(self.type_ordi, 2)], soumettre=True)
        with self.assertRaises(ValidationError):
            services.autoriser_ligne(bs2.lignes.get(), self.dsid, 2)


# =====================================================================
# SORTIE PHYSIQUE (CAME)
# =====================================================================
class SortieTests(BaseTest):

    def test_sortie_impossible_tant_que_le_dca_n_a_pas_traite_toutes_les_lignes(self):
        """Une ligne déjà validée ne peut pas sortir tant que le DCA n'a pas fini d'examiner le BS."""
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        bs = self._bs([(self.type_encre, 5), (self.type_ordi, 2)], soumettre=True)
        l_encre, l_ordi = bs.lignes.order_by('id')
        services.autoriser_ligne(l_encre, self.dsid, 5)
        services.autoriser_ligne(l_ordi, self.dsid, 2)
        services.valider_ligne(l_encre, self.dca, 5)      # une seule ligne validée sur deux
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'en_attente_validation')
        with self.assertRaises(ValidationError):
            self._sortir(bs)
        self.assertFalse(Sortie.objects.exists())
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 20)
        services.valider_ligne(l_ordi, self.dca, 2)       # le DCA termine : la sortie devient possible
        bs.refresh_from_db()
        self._sortir(bs)

    def test_sortie_impossible_avant_validation(self):
        self._entrer(self.type_encre, 20)
        for etat in ('brouillon', 'en_attente_autorisation', 'en_attente_validation'):
            bs = self._bs([(self.type_encre, 5)])
            if etat != 'brouillon':
                services.soumettre_bon_sortie(bs, self.demandeur)
            if etat == 'en_attente_validation':
                services.autoriser_ligne(bs.lignes.get(), self.dsid, 5)
            bs.refresh_from_db()
            self.assertEqual(bs.statut, etat)
            with self.assertRaises(ValidationError):
                self._sortir(bs)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 20)
        self.assertEqual(Sortie.objects.count(), 0)

    def test_quantites_reelles_livrees_et_sortie_quantite_somme(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        bs = self._valide([(self.type_encre, 10), (self.type_ordi, 3)])
        l_encre, l_ordi = bs.lignes.order_by('id')
        sortie = self._sortir(bs, {l_encre.id: 8, l_ordi.id: 3})  # le CAME ne livre que 8 sur 10
        self.assertEqual(sortie.quantite, 11, "Sortie.quantite = somme des LigneSortie.quantite_livree")
        self.assertEqual(
            sorted(sortie.lignes.values_list('quantite_livree', flat=True)), [3, 8])
        self.type_encre.refresh_from_db()
        self.type_ordi.refresh_from_db()
        self.assertEqual((self.type_encre.quantite_stock, self.type_ordi.quantite_stock), (12, 2))
        bs.refresh_from_db()
        self.assertEqual(bs.statut, 'sorti')
        self.assertTrue(all(l.etat_ligne == 'sortie' for l in bs.lignes.all()))

    def test_livraison_superieure_au_valide_refusee(self):
        self._entrer(self.type_encre, 20)
        bs = self._valide([(self.type_encre, 5)])
        with self.assertRaises(ValidationError):
            self._sortir(bs, {bs.lignes.get().id: 6})
        self.assertFalse(Sortie.objects.exists())

    def test_quantite_validee_est_utilisee_par_defaut(self):
        self._entrer(self.type_encre, 20)
        bs = self._bs([(self.type_encre, 10)], soumettre=True)
        ligne = bs.lignes.get()
        services.autoriser_ligne(ligne, self.dsid, 10)
        services.valider_ligne(ligne, self.dca, 6, motif='budget')
        sortie = self._sortir(bs)
        self.assertEqual(sortie.quantite, 6)
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 14)

    def test_lien_ligne_sortie_vers_ligne_bsortie(self):
        self._entrer(self.type_encre, 20)
        bs = self._valide([(self.type_encre, 5)])
        sortie = self._sortir(bs)
        ls = sortie.lignes.get()
        self.assertEqual(ls.ligne_bsortie, bs.lignes.get())
        self.assertEqual(ls.quantite_livree, 5)
        self.assertFalse(hasattr(ls, 'quantite_demandee'))
        self.assertFalse(hasattr(ls, 'quantite_autorisee'))
        self.assertEqual(bs.lignes.get().ligne_sortie, ls)

    def test_un_bs_ne_sort_qu_une_fois(self):
        self._entrer(self.type_encre, 20)
        bs = self._valide([(self.type_encre, 5)])
        self._sortir(bs)
        with self.assertRaises(ValidationError):
            self._sortir(bs)

    def test_mouvements_de_sortie_portent_l_entite_et_l_utilisateur(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 3)
        bs = self._valide([(self.type_encre, 5), (self.type_ordi, 2)])
        self._sortir(bs)
        for m in Mouvement.objects.filter(type_mouvement='sortie'):
            self.assertEqual(m.entite, self.entite)
            self.assertEqual(m.utilisateur, self.came)
            m.clean()
        self.assertEqual(Mouvement.objects.filter(type_mouvement='sortie', article__isnull=False).count(), 2)
        self.assertEqual(
            Mouvement.objects.get(type_mouvement='sortie', type_article=self.type_encre).quantite, 5)

    def test_sortie_que_de_consommables_sans_article(self):
        self._entrer(self.type_encre, 20)
        sortie = self._sortir(self._valide([(self.type_encre, 5)]))
        self.assertEqual(sortie.articles.count(), 0)

    def test_stock_physique_corrige_a_la_baisse_bloque_la_sortie(self):
        self._entrer(self.type_encre, 20)
        bs = self._valide([(self.type_encre, 10)])
        TypeArticle.objects.filter(pk=self.type_encre.pk).update(quantite_stock=4)  # correction externe
        with self.assertRaises(ValidationError):
            self._sortir(bs)
        self.assertFalse(Sortie.objects.exists())


# =====================================================================
# API REST
# =====================================================================
class ApiTests(BaseTest):

    def _client(self, user=None):
        c = APIClient()
        if user:
            c.force_authenticate(user)
        return c

    def test_api_protegee(self):
        self.assertEqual(self._client().get('/api/types-article/').status_code, 403)

    def test_utilisateur_desactive_refuse(self):
        self.dsid.actif = False
        self.dsid.save()
        c = APIClient()
        self.assertTrue(c.login(username='dsid', password='x') is False)

    def test_workflow_complet_via_api(self):
        self._entrer(self.type_encre, 20)
        self._entrer(self.type_ordi, 5)
        dem, dsid, dca, came = (self._client(u) for u in (self.demandeur, self.dsid, self.dca, self.came))

        r = dem.post('/api/bons-sortie/', {'reference_bs': 'BS-API', 'date_bs': '2026-10-10',
                                            'entite': self.entite.id, 'statut': 'valide'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['statut'], 'brouillon', "le statut envoyé par le client est ignoré")
        self.assertEqual(r.data['utilisateur'], self.demandeur.id)
        bs_id = r.data['id']

        for t, q in ((self.type_encre, 10), (self.type_ordi, 2)):
            r = dem.post(f'/api/bons-sortie/{bs_id}/ajouter_ligne/', {'type_article': t.id, 'quantite_demandee': q}, format='json')
            self.assertEqual(r.status_code, 201, r.content)

        r = dem.post(f'/api/bons-sortie/{bs_id}/soumettre/')
        self.assertEqual((r.status_code, r.data['statut']), (200, 'en_attente_autorisation'))
        # plus de modification ni d'ajout de ligne après soumission
        self.assertEqual(dem.post(f'/api/bons-sortie/{bs_id}/ajouter_ligne/',
                                  {'type_article': self.type_encre.id, 'quantite_demandee': 1}, format='json').status_code, 400)
        self.assertEqual(dem.patch(f'/api/bons-sortie/{bs_id}/', {'document': 'x'}, format='json').status_code, 400)

        l_encre, l_ordi = LigneBSortie.objects.filter(bon_sortie_id=bs_id).order_by('id')
        # rôles : le demandeur ne peut pas autoriser
        self.assertEqual(dem.post(f'/api/lignes-bsortie/{l_encre.id}/autoriser/', {'quantite': 10}, format='json').status_code, 403)
        # autorisation partielle sans motif -> 400
        self.assertEqual(dsid.post(f'/api/lignes-bsortie/{l_encre.id}/autoriser/', {'quantite': 7}, format='json').status_code, 400)
        r = dsid.post(f'/api/lignes-bsortie/{l_encre.id}/autoriser/', {'quantite': 7, 'motif': 'stock limité'}, format='json')
        self.assertEqual((r.status_code, r.data['etat_ligne'], r.data['quantite_autorisee']), (200, 'autorisee', 7))
        r = dsid.post(f'/api/lignes-bsortie/{l_ordi.id}/autoriser/', {'quantite': 0, 'motif': 'refus'}, format='json')
        self.assertEqual(r.data['etat_ligne'], 'refusee')

        # le DCA ne voit que les lignes à valider
        a_valider = dca.get(f'/api/lignes-bsortie/?bon_sortie={bs_id}&etat_ligne=autorisee').data
        a_valider = a_valider['results'] if isinstance(a_valider, dict) else a_valider
        self.assertEqual([l['id'] for l in a_valider], [l_encre.id])
        self.assertEqual(dca.post(f'/api/lignes-bsortie/{l_ordi.id}/valider/', {'quantite': 2}, format='json').status_code, 400)
        r = dca.post(f'/api/lignes-bsortie/{l_encre.id}/valider/', {'quantite': 6, 'motif': 'budget'}, format='json')
        self.assertEqual((r.status_code, r.data['etat_ligne'], r.data['quantite_validee']), (200, 'validee', 6))
        self.assertEqual(dca.get(f'/api/bons-sortie/{bs_id}/').data['statut'], 'valide')

        # stock : physique inchangé, réservé 6
        s = dsid.get(f'/api/types-article/{self.type_encre.id}/stock/').data
        self.assertEqual((s['quantite_stock'], s['quantite_reservee'], s['stock_disponible_pour_autorisation']), (20, 6, 14))

        # sortie : refusée tant que le rôle n'est pas CAME
        corps = {'bon_sortie': bs_id, 'date_sortie': '2026-10-11', 'livraisons': [{'ligne_bsortie': l_encre.id, 'quantite_livree': 5}]}
        self.assertEqual(dca.post('/api/sorties/effectuer/', corps, format='json').status_code, 403)
        r = came.post('/api/sorties/effectuer/', corps, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data['quantite'], 5)
        s = came.get(f'/api/types-article/{self.type_encre.id}/stock/').data
        self.assertEqual((s['quantite_stock'], s['quantite_reservee']), (15, 0))
        self.assertEqual(came.post('/api/sorties/effectuer/', corps, format='json').status_code, 400)  # une seule fois

        # historique : décisions et mouvements traçables
        iv = came.get(f'/api/interventions/?ligne_bsortie={l_encre.id}').data
        iv = iv['results'] if isinstance(iv, dict) else iv
        self.assertEqual(sorted(i['role_intervention'] for i in iv), ['autorisation', 'validation'])
        mv = came.get(f'/api/mouvements/?type_mouvement=sortie&entite={self.entite.id}').data
        mv = mv['results'] if isinstance(mv, dict) else mv
        self.assertEqual(len(mv), 1)

    def test_effectuer_bs_non_valide_refuse(self):
        bs = self._bs([(self.type_encre, 5)], soumettre=True)
        r = self._client(self.came).post('/api/sorties/effectuer/', {'bon_sortie': bs.id, 'date_sortie': '2026-10-11'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_pas_de_creation_directe_de_sortie_ni_mouvement_ni_article(self):
        c = self._client(self.root)
        for url in ('/api/sorties/', '/api/mouvements/', '/api/articles/', '/api/interventions/'):
            self.assertEqual(c.post(url, {}, format='json').status_code, 405, url)

    def test_ligne_bsortie_non_modifiable_directement(self):
        bs = self._bs([(self.type_encre, 5)])
        c = self._client(self.root)
        self.assertEqual(c.patch(f'/api/lignes-bsortie/{bs.lignes.get().id}/', {'etat_ligne': 'validee'}, format='json').status_code, 405)

    def test_entree_via_api_fournisseur_obligatoire_et_lignes(self):
        c = self._client(self.dsid)
        base = {'date_entree': '2026-10-10', 'ref_entree': 'E-API', 'origine': 'achat'}
        self.assertEqual(c.post('/api/entrees/', base, format='json').status_code, 400)  # sans fournisseur
        r = c.post('/api/entrees/', {**base, 'fournisseur': self.fournisseur.id}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        eid = r.data['id']
        r = c.post(f'/api/entrees/{eid}/ajouter_ligne/', {'type_article': self.type_ordi.id, 'quantite': 3}, format='json')
        self.assertEqual((r.status_code, len(r.data['articles_crees']), r.data['stock_apres']), (201, 3, 3))
        r = c.post(f'/api/entrees/{eid}/ajouter_ligne/', {'type_article': self.type_encre.id, 'quantite': 50}, format='json')
        self.assertEqual((len(r.data['articles_crees']), r.data['stock_apres']), (0, 50))
        self.assertEqual(c.delete(f'/api/entrees/{eid}/').status_code, 405, "jamais de suppression d'une entrée")

    def test_referentiels_unicite_via_api(self):
        c = self._client(self.dsid)
        self.assertEqual(c.post('/api/categories/', {'nom_categorie': 'Informatique'}, format='json').status_code, 400)
        r = c.post('/api/types-article/', {'nom_type_article': 'Ordinateur portable', 'categorie': self.categorie.id}, format='json')
        self.assertEqual(r.status_code, 400)
        r = c.post('/api/entites/', {'nom_entite': 'Agence Tsaralalana', 'sigle_entite': '10102', 'type_entite': 'agence'}, format='json')
        self.assertEqual(r.status_code, 201)
        r = c.post('/api/fournisseurs/', {'nom_fournisseur': 'Nouveau'}, format='json')
        self.assertEqual(r.status_code, 201)

    def test_suppression_d_un_element_utilise_est_refusee_proprement(self):
        r = self._client(self.root).delete(f'/api/categories/{self.categorie.id}/')
        self.assertEqual(r.status_code, 409)

    def test_quantite_stock_non_modifiable_par_api(self):
        c = self._client(self.root)
        c.patch(f'/api/types-article/{self.type_encre.id}/', {'quantite_stock': 999}, format='json')
        self.type_encre.refresh_from_db()
        self.assertEqual(self.type_encre.quantite_stock, 0)


# =====================================================================
# ADMIN (non-régression : le bug de l'admin qui contournait services.py)
# =====================================================================
class AdminTests(BaseTest):

    def setUp(self):
        super().setUp()
        self.client.force_login(self.root)

    def test_toutes_les_pages_admin_s_affichent(self):
        from django.contrib import admin as dj_admin
        for modele, model_admin in dj_admin.site._registry.items():
            if modele._meta.app_label != 'inventaire':
                continue
            nom = f'admin:inventaire_{modele._meta.model_name}'
            r = self.client.get(reverse(f'{nom}_changelist'))
            self.assertEqual(r.status_code, 200, f'{nom}_changelist')
            if model_admin.has_add_permission(_FausseRequete(self.root)):
                r = self.client.get(reverse(f'{nom}_add'))
                self.assertEqual(r.status_code, 200, f'{nom}_add')

    def test_entree_admin_applique_la_logique_metier(self):
        data = {
            'date_entree': '2026-10-10', 'document': 'DOC', 'ref_entree': 'ADM-1', 'origine': 'achat',
            'fournisseur': self.fournisseur.id,
            'lignes-TOTAL_FORMS': '2', 'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-type_article': self.type_ordi.id, 'lignes-0-quantite': '3',
            'lignes-1-type_article': self.type_encre.id, 'lignes-1-quantite': '50',
            '_save': 'Enregistrer',
        }
        r = self.client.post(reverse('admin:inventaire_entree_add'), data, follow=True)
        self.assertEqual(r.status_code, 200)
        entree = Entree.objects.get(ref_entree='ADM-1')
        self.assertEqual(entree.utilisateur, self.root, "le compte connecté est l'auteur")
        self.type_ordi.refresh_from_db()
        self.type_encre.refresh_from_db()
        self.assertEqual((self.type_ordi.quantite_stock, self.type_encre.quantite_stock), (3, 50))
        self.assertEqual(Article.objects.filter(ligne_entree__entree=entree).count(), 3)
        self.assertEqual(Mouvement.objects.count(), 4)  # 3 articles + 1 mouvement consommable

    def test_bon_sortie_admin_cree_un_brouillon_non_modifiable_a_la_main(self):
        data = {
            'reference_bs': 'ADM-BS', 'date_bs': '2026-10-10', 'entite': self.entite.id,
            'statut': 'valide',  # tentative de forcer le statut : doit être ignorée
            'lignes-TOTAL_FORMS': '1', 'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-type_article': self.type_encre.id, 'lignes-0-quantite_demandee': '4',
            '_save': 'Enregistrer',
        }
        r = self.client.post(reverse('admin:inventaire_bonsortie_add'), data, follow=True)
        self.assertEqual(r.status_code, 200)
        bs = BonSortie.objects.get(reference_bs='ADM-BS')
        self.assertEqual((bs.statut, bs.utilisateur), ('brouillon', self.root))
        ligne = bs.lignes.get()
        self.assertEqual((ligne.quantite_demandee, ligne.etat_ligne), (4, 'demandee'))

    def test_historique_non_modifiable_dans_l_admin(self):
        for nom in ('sortie', 'lignesortie', 'mouvement', 'intervient', 'lignebsortie'):
            self.assertEqual(self.client.get(reverse(f'admin:inventaire_{nom}_add')).status_code, 403, nom)


class _FausseRequete:
    def __init__(self, user):
        self.user = user
