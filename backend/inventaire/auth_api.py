
import logging

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

Utilisateur = get_user_model()


def _role_libelle(user):
    correspondances = {
        'admin': 'Administrateur',
        'agent_dsid': 'Agent DSID',
        'agent_validation': 'Ancien Agent Validation (DCA)',
        'dg': 'Directeur Général (DG)',
        'dga': 'Directeur Général Adjoint (DGA)',
        'directeur_dsid': 'Directeur DSID',
        'agent_came': 'Agent CAME',
        'demandeur': 'Demandeur',
        'agent_direction': 'Agent Direction',
        'auditeur': 'Auditeur',
    }

    if user.is_superuser:
        return 'Administrateur'

    return correspondances.get(user.role, user.role)


def _profil(user):
    entites = list(user.entites.all())

    entite_unique = None
    if len(entites) == 1:
        entite = entites[0]
        entite_unique = {
            'id': entite.id,
            'nom_entite': entite.nom_entite,
            'type_entite': entite.type_entite,
        }

    return {
        'id': user.id,
        'nom_complet': f'{user.first_name} {user.last_name}'.strip(),
        'email': user.email,
        'role': user.role,
        'role_libelle': _role_libelle(user),
        'entites': [entite.id for entite in entites],
        'entite_unique': entite_unique,
        'authentifie': True,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'doit_changer_mot_de_passe': user.doit_changer_mot_de_passe,
    }


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_view(request):
    """
    Connexion avec le nom complet et le mot de passe.

    Le username reste interne à Django : il n'est pas demandé à l'agent.
    Si plusieurs comptes ont le même nom, le mot de passe permet de
    retrouver le compte correspondant.
    """
    nom_complet = str(request.data.get('nom') or '').strip()
    password = str(request.data.get('password') or '')

    if not nom_complet or not password:
        return Response(
            {'erreur': 'Le nom et le mot de passe sont obligatoires.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    morceaux = nom_complet.split()
    if len(morceaux) < 2:
        return Response(
            {'erreur': 'Veuillez saisir votre prénom et votre nom.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Le premier élément correspond au prénom, le reste au nom.
    first_name = morceaux[0]
    last_name = ' '.join(morceaux[1:])

    candidats = Utilisateur.objects.filter(
        first_name__iexact=first_name,
        last_name__iexact=last_name,
        actif=True,
        is_active=True,
    )

    user = None

    for candidat in candidats:
        utilisateur_authentifie = authenticate(
            request,
            username=candidat.username,
            password=password,
        )
        if utilisateur_authentifie is not None:
            user = utilisateur_authentifie
            break

    if user is None:
        return Response(
            {'erreur': 'Nom ou mot de passe incorrect, ou compte désactivé.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if (
        user.doit_changer_mot_de_passe
        and user.mot_de_passe_temporaire_expire_le
        and timezone.now() > user.mot_de_passe_temporaire_expire_le
    ):
        return Response(
            {
                'erreur': (
                    "Le mot de passe temporaire a expiré. "
                    "Contactez l'administrateur pour en recevoir un nouveau."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    django_login(request, user)

    return Response(_profil(user))


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated:
        return Response({'authentifie': False})

    return Response(_profil(request.user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def changer_mot_de_passe(request):
    ancien = str(request.data.get('ancien_mot_de_passe') or '')
    nouveau = str(request.data.get('nouveau_mot_de_passe') or '')
    confirmation = str(request.data.get('confirmation') or '')

    user = request.user

    if not user.check_password(ancien):
        return Response(
            {'erreur': 'Le mot de passe actuel est incorrect.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if nouveau != confirmation:
        return Response(
            {'erreur': 'Les deux nouveaux mots de passe ne correspondent pas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(nouveau, user)
    except Exception as exc:
        messages = getattr(exc, 'messages', ['Mot de passe invalide.'])
        return Response(
            {'erreur': ' '.join(messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(nouveau)
    user.doit_changer_mot_de_passe = False
    user.mot_de_passe_temporaire_expire_le = None
    user.save()

    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, user)

    return Response(_profil(user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    django_logout(request)
    return Response({'deconnecte': True})
