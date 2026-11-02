"""
Logique métier de PAOSITRA SMART ASSET (Mois 2).

Toutes les règles sensibles vivent ICI, jamais dans les vues ni dans l'admin :
- entrée en stock (individualisé / consommable) ;
- workflow du Bon de Sortie, ligne par ligne :
      Demande -> Autorisation DSID -> Validation DCA -> Sortie physique CAME ;
- stock réservé / stock disponible pour autorisation ;
- sortie physique (seule opération qui diminue réellement le stock).

Chaque fonction qui écrit en base le fait dans UNE transaction : soit tout
réussit, soit rien n'est écrit. Les vérifications se font AVANT les écritures.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import (
    Article, BonSortie, Intervient, LigneBSortie, LigneEntree,
    LigneSortie, Mouvement, Sortie, TypeArticle,
)

# Rôles autorisés pour chaque étape du workflow (is_superuser est toujours accepté).
# PROPOSITION — À VALIDER : contrôle de rôle minimal, pas de système de permissions détaillé.
ROLES_SOUMISSION = {'demandeur', 'agent_direction'}
ROLES_AUTORISATION = {'agent_dsid'}
ROLES_VALIDATION = {'agent_validation'}
ROLES_SORTIE = {'agent_came'}


def _verifier_role(utilisateur, roles_autorises, action):
    if not utilisateur.actif:
        raise PermissionDenied("Compte désactivé.")
    if utilisateur.is_superuser or utilisateur.role in roles_autorises:
        return
    raise PermissionDenied(f"Votre rôle ne permet pas de {action}.")


def _verrouiller_type(type_article):
    """Relit le type en base avec un verrou : sérialise les opérations de stock concurrentes."""
    return TypeArticle.objects.select_for_update().get(pk=type_article.pk)


# ---------------------------------------------------------------------------
# STOCK
# ---------------------------------------------------------------------------

def stock_disponible(type_article: TypeArticle) -> int:
    """Stock PHYSIQUE du type (TypeArticle.quantite_stock)."""
    return type_article.quantite_stock


def stock_reserve(type_article: TypeArticle) -> int:
    """
    Quantité actuellement réservée par des lignes de BS pas encore sorties :
      - ligne AUTORISEE (pas encore validée) -> quantite_autorisee
      - ligne VALIDEE                         -> quantite_validee
      - lignes demandée / refusée / rejetée / sortie -> 0
    Valeur calculée, jamais stockée.
    """
    lignes = LigneBSortie.objects.filter(type_article=type_article)
    autorisees = lignes.filter(etat_ligne='autorisee').aggregate(t=Sum('quantite_autorisee'))['t'] or 0
    validees = lignes.filter(etat_ligne='validee').aggregate(t=Sum('quantite_validee'))['t'] or 0
    return autorisees + validees


def stock_disponible_pour_autorisation(type_article: TypeArticle) -> int:
    """Stock physique - stock réservé : ce que le DSID peut encore autoriser."""
    return type_article.quantite_stock - stock_reserve(type_article)


# ---------------------------------------------------------------------------
# ENTRÉES
# ---------------------------------------------------------------------------

def enregistrer_ligne_entree(entree, type_article: TypeArticle, quantite: int, utilisateur, nom_agent=''):
    """
    - TypeArticle.quantite_stock augmente TOUJOURS de `quantite` (stock global du type).
    - Type individualisé : en plus, `quantite` Article distincts + un Mouvement 'entree' par article.
    - Consommable : un seul Mouvement portant la quantité, aucun Article.
    """
    if quantite <= 0:
        raise ValidationError("La quantité doit être strictement positive.")

    with transaction.atomic():
        type_verrouille = _verrouiller_type(type_article)
        ligne = LigneEntree.objects.create(entree=entree, type_article=type_verrouille, quantite=quantite)

        type_verrouille.quantite_stock += quantite
        type_verrouille.save(update_fields=['quantite_stock'])
        type_article.quantite_stock = type_verrouille.quantite_stock

        if type_verrouille.gestion_individuelle:
            articles_crees = []
            for i in range(quantite):
                article = Article.objects.create(
                    ref_article=f"{entree.ref_entree}-{type_verrouille.id}-{i + 1:03d}",
                    type_article=type_verrouille,
                    ligne_entree=ligne,
                )
                Mouvement.objects.create(
                    type_mouvement='entree',
                    article=article,
                    utilisateur=utilisateur,
                    utilisateur_nom_saisi=nom_agent or utilisateur.get_full_name() or utilisateur.username,
                    utilisateur_role_saisi=utilisateur.get_role_display(),
                    operation_ref=f"ENT-{entree.ref_entree}-L{ligne.id}",
                )
                articles_crees.append(article)
            return ligne, articles_crees

        Mouvement.objects.create(
            type_mouvement='entree',
            type_article=type_verrouille,
            quantite=quantite,
            utilisateur=utilisateur,
            utilisateur_nom_saisi=nom_agent or utilisateur.get_full_name() or utilisateur.username,
            utilisateur_role_saisi=utilisateur.get_role_display(),
            operation_ref=f"ENT-{entree.ref_entree}-L{ligne.id}",
        )
        return ligne, []


# ---------------------------------------------------------------------------
# WORKFLOW DU BON DE SORTIE
# ---------------------------------------------------------------------------

def _recalculer_statut(bon_sortie):
    """
    Met à jour BonSortie.statut à partir de l'état des lignes (jamais saisi à la main).
      EN_ATTENTE_AUTORISATION : tant qu'une ligne est encore 'demandee'.
        -> toutes traitées par le DSID : EN_ATTENTE_VALIDATION s'il reste une ligne
           autorisée, sinon REFUSE (toutes refusées).
      EN_ATTENTE_VALIDATION : tant qu'une ligne est encore 'autorisee'.
        -> toutes traitées par le DCA : VALIDE s'il reste une ligne validée,
           sinon REFUSE (tout refusé/rejeté).
    Les lignes refusées/rejetées ne bloquent jamais les autres lignes.
    """
    etats = list(bon_sortie.lignes.values_list('etat_ligne', flat=True))
    if bon_sortie.statut == 'en_attente_autorisation':
        if 'demandee' in etats:
            return
        bon_sortie.statut = 'en_attente_validation' if 'autorisee' in etats else 'refuse'
    elif bon_sortie.statut == 'en_attente_validation':
        if 'autorisee' in etats:
            return
        bon_sortie.statut = 'valide' if 'validee' in etats else 'refuse'
    else:
        return
    bon_sortie.save(update_fields=['statut'])


def soumettre_bon_sortie(bon_sortie, utilisateur):
    """BROUILLON -> EN_ATTENTE_AUTORISATION (par le demandeur qui a créé le BS)."""
    _verifier_role(utilisateur, ROLES_SOUMISSION, "soumettre un bon de sortie")
    with transaction.atomic():
        bs = BonSortie.objects.select_for_update().get(pk=bon_sortie.pk)
        if not utilisateur.is_superuser and bs.utilisateur_id != utilisateur.id:
            raise PermissionDenied("Seul le créateur du bon de sortie peut le soumettre.")
        if bs.statut != 'brouillon':
            raise ValidationError(f"Ce bon de sortie n'est plus un brouillon (statut : {bs.get_statut_display()}).")
        if not bs.lignes.exists():
            raise ValidationError("Un bon de sortie doit contenir au moins une ligne pour être soumis.")
        bs.statut = 'en_attente_autorisation'
        bs.save(update_fields=['statut'])
    bon_sortie.statut = bs.statut
    return bon_sortie


def autoriser_ligne(ligne, utilisateur, quantite, motif=''):
    """
    Décision du DSID sur UNE ligne : autoriser la quantité demandée, une quantité
    inférieure, ou refuser (quantite = 0). Motif obligatoire si quantité != demandée.
    L'autorisation est bornée par le stock disponible pour autorisation
    (stock physique - stock déjà réservé) : pas de sur-réservation entre BS concurrents.
    """
    _verifier_role(utilisateur, ROLES_AUTORISATION, "autoriser une ligne de bon de sortie")
    motif = (motif or '').strip()
    with transaction.atomic():
        bs = BonSortie.objects.select_for_update().get(pk=ligne.bon_sortie_id)
        ligne_db = LigneBSortie.objects.select_for_update().get(pk=ligne.pk)
        if bs.statut != 'en_attente_autorisation':
            raise ValidationError(f"Autorisation impossible : le bon de sortie est '{bs.get_statut_display()}'.")
        if ligne_db.etat_ligne != 'demandee':
            raise ValidationError("Cette ligne a déjà été traitée par le DSID.")
        if quantite < 0 or quantite > ligne_db.quantite_demandee:
            raise ValidationError(
                f"La quantité autorisée doit être comprise entre 0 et la quantité demandée ({ligne_db.quantite_demandee})."
            )
        if quantite != ligne_db.quantite_demandee and not motif:
            raise ValidationError("Un motif est obligatoire quand la quantité autorisée diffère de la quantité demandée (ou en cas de refus).")

        if quantite > 0:
            type_verrouille = _verrouiller_type(ligne_db.type_article)
            reserve = stock_reserve(type_verrouille)
            disponible = type_verrouille.quantite_stock - reserve
            if quantite > disponible:
                raise ValidationError(
                    f"Autorisation impossible pour '{type_verrouille}' : quantité {quantite} > stock disponible "
                    f"pour autorisation {disponible} (stock physique {type_verrouille.quantite_stock}, déjà réservé {reserve})."
                )

        Intervient.objects.create(
            ligne_bsortie=ligne_db, utilisateur=utilisateur, role_intervention='autorisation',
            quantite_decidee=quantite, motif=motif or None,
        )
        ligne_db.quantite_autorisee = quantite
        ligne_db.etat_ligne = 'autorisee' if quantite > 0 else 'refusee'
        ligne_db.save(update_fields=['quantite_autorisee', 'etat_ligne'])
        _recalculer_statut(bs)
    return ligne_db


def valider_ligne(ligne, utilisateur, quantite, motif=''):
    """
    Décision du DCA sur une ligne AUTORISEE : valider la quantité autorisée, la
    diminuer, ou rejeter (quantite = 0). Motif obligatoire si quantité != autorisée.
    Une ligne refusée par le DSID n'est jamais proposée au DCA.
    PROPOSITION — À VALIDER : le DCA ne peut pas valider plus que la quantité autorisée
    (sinon la réservation de stock ne serait plus garantie).
    """
    _verifier_role(utilisateur, ROLES_VALIDATION, "valider une ligne de bon de sortie")
    motif = (motif or '').strip()
    with transaction.atomic():
        bs = BonSortie.objects.select_for_update().get(pk=ligne.bon_sortie_id)
        ligne_db = LigneBSortie.objects.select_for_update().get(pk=ligne.pk)
        if bs.statut != 'en_attente_validation':
            raise ValidationError(f"Validation impossible : le bon de sortie est '{bs.get_statut_display()}'.")
        if ligne_db.etat_ligne != 'autorisee':
            raise ValidationError("Seules les lignes autorisées par le DSID peuvent être validées.")
        if quantite < 0 or quantite > ligne_db.quantite_autorisee:
            raise ValidationError(
                f"La quantité validée doit être comprise entre 0 et la quantité autorisée ({ligne_db.quantite_autorisee})."
            )
        if quantite != ligne_db.quantite_autorisee and not motif:
            raise ValidationError("Un motif est obligatoire quand la quantité validée diffère de la quantité autorisée (ou en cas de rejet).")

        Intervient.objects.create(
            ligne_bsortie=ligne_db, utilisateur=utilisateur, role_intervention='validation',
            quantite_decidee=quantite, motif=motif or None,
        )
        ligne_db.quantite_validee = quantite
        ligne_db.etat_ligne = 'validee' if quantite > 0 else 'rejetee'
        ligne_db.save(update_fields=['quantite_validee', 'etat_ligne'])
        _recalculer_statut(bs)
    return ligne_db


# ---------------------------------------------------------------------------
# SORTIE PHYSIQUE (CAME)
# ---------------------------------------------------------------------------

def effectuer_sortie(bon_sortie, date_sortie, utilisateur, livraisons=None, nom_agent=''):
    """
    Sortie physique réalisée par le CAME, uniquement pour un BS VALIDE.
    `livraisons` : {id_ligne_bsortie: quantite_livree} ; par défaut, chaque ligne
    validée est livrée pour sa quantite_validee. La quantité livrée ne peut pas
    dépasser la quantité validée.
    PROPOSITION — À VALIDER : une ligne peut être livrée à 0 (non livrée, tracée dans
    LigneSortie) tant que le total livré est > 0.

    C'est la SEULE opération qui diminue réellement le stock. Tout est vérifié
    AVANT d'écrire ; transaction unique : aucune sortie partielle ne peut subsister.
    Sortie.quantite = somme des quantités livrées.
    """
    _verifier_role(utilisateur, ROLES_SORTIE, "effectuer une sortie physique")
    livraisons = {int(k): int(v) for k, v in (livraisons or {}).items()}

    with transaction.atomic():
        bs = BonSortie.objects.select_for_update().get(pk=bon_sortie.pk)
        if bs.statut != 'valide':
            raise ValidationError(
                f"La sortie n'est possible que pour un bon de sortie validé (statut actuel : {bs.get_statut_display()})."
            )
        if Sortie.objects.filter(bon_sortie=bs).exists():
            raise ValidationError("Ce bon de sortie a déjà une sortie enregistrée.")

        lignes = list(bs.lignes.filter(etat_ligne='validee').order_by('id'))
        if not lignes:
            raise ValidationError("Aucune ligne validée à livrer sur ce bon de sortie.")
        inconnues = set(livraisons) - {l.id for l in lignes}
        if inconnues:
            raise ValidationError(f"Ligne(s) inconnue(s) ou non validée(s) dans les livraisons : {sorted(inconnues)}.")

        plan = []
        for ligne in lignes:
            livree = livraisons.get(ligne.id, ligne.quantite_validee)
            if livree < 0 or livree > ligne.quantite_validee:
                raise ValidationError(
                    f"Quantité livrée invalide pour la ligne {ligne.id} : {livree} "
                    f"(maximum = quantité validée {ligne.quantite_validee})."
                )
            plan.append((ligne, livree))
        total = sum(livree for _, livree in plan)
        if total == 0:
            raise ValidationError("Aucune quantité livrée : la sortie n'a pas lieu d'être enregistrée.")

        # Verrou des types concernés (ordre croissant d'id : pas d'interblocage).
        besoins = {}
        for ligne, livree in plan:
            besoins[ligne.type_article_id] = besoins.get(ligne.type_article_id, 0) + livree
        types = {tid: TypeArticle.objects.select_for_update().get(pk=tid) for tid in sorted(besoins)}

        pools = {}
        for tid, besoin in besoins.items():
            t = types[tid]
            if besoin > t.quantite_stock:
                raise ValidationError(
                    f"Sortie impossible pour '{t}' : quantité à livrer {besoin} > stock physique {t.quantite_stock}."
                )
            if t.gestion_individuelle:
                pool = list(
                    Article.objects.filter(type_article=t).exclude(sorties__isnull=False).order_by('id')[:besoin]
                )
                if len(pool) < besoin:
                    raise ValidationError(
                        f"Incohérence pour '{t}' : {besoin} article(s) à sortir mais seulement {len(pool)} disponible(s)."
                    )
                pools[tid] = pool

        # --- Écritures (toutes les vérifications sont passées) ---
        sortie = Sortie.objects.create(
            bon_sortie=bs, date_sortie=date_sortie, quantite=total, ref_sortie=f"SOR-{bs.reference_bs}",
        )
        for ligne, livree in plan:
            t = types[ligne.type_article_id]
            LigneSortie.objects.create(
                sortie=sortie, ligne_bsortie=ligne, type_article=t, quantite_livree=livree,
            )
            if livree > 0:
                t.quantite_stock -= livree
                if t.gestion_individuelle:
                    choisis, pools[t.id] = pools[t.id][:livree], pools[t.id][livree:]
                    sortie.articles.add(*choisis)
                    for article in choisis:
                        Mouvement.objects.create(
                            type_mouvement='sortie',
                            article=article,
                            utilisateur=utilisateur,
                            entite=bs.entite,
                            utilisateur_nom_saisi=nom_agent or utilisateur.get_full_name() or utilisateur.username,
                            utilisateur_role_saisi=utilisateur.get_role_display(),
                            operation_ref=sortie.ref_sortie,
                        )
                else:
                    Mouvement.objects.create(
                        type_mouvement='sortie',
                        type_article=t,
                        quantite=livree,
                        utilisateur=utilisateur,
                        entite=bs.entite,
                        utilisateur_nom_saisi=nom_agent or utilisateur.get_full_name() or utilisateur.username,
                        utilisateur_role_saisi=utilisateur.get_role_display(),
                        operation_ref=sortie.ref_sortie,
                    )
            ligne.etat_ligne = 'sortie'
            ligne.save(update_fields=['etat_ligne'])
        for t in types.values():
            t.save(update_fields=['quantite_stock'])

        bs.statut = 'sorti'
        bs.save(update_fields=['statut'])
    return sortie
