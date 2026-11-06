from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


def _role_libelle(user):
    correspondances = {
        'admin': 'Administrateur',
        'agent_dsid': 'Agent DSID',
        'agent_validation': 'Agent Validation',
        'agent_came': 'Agent CAME',
        'demandeur': 'Demandeur',
        'agent_direction': 'Agent Direction',
        'auditeur': 'Auditeur',
    }

    username = user.username.lower()

    correspondances_comptes = {
        'came1': 'Agent CAME',
        'dsid1': 'Agent DSID',
        'dca1': 'Agent Validation',
        'auditeur1': 'Auditeur',
        'admin': 'Administrateur',
    }

    if username in correspondances_comptes:
        return correspondances_comptes[username]

    if user.is_superuser:
        return 'Administrateur'

    return correspondances.get(user.role, user.role)


def _profil(user, request=None):
    nom_saisi = None

    if request:
        nom_saisi = request.session.get('agent_nom_saisi')

    if not nom_saisi:
        nom_saisi = (
            f"{user.first_name} {user.last_name}".strip()
            or user.username
        )

    return {
        'id': user.id,
        'username': user.username,
        'nom_complet': nom_saisi,
        'role': getattr(user, 'role', ''),
        'role_libelle': _role_libelle(user),
        'entites': list(user.entites.values_list('id', flat=True)) if hasattr(user, 'entites') else [],
        'entite_unique': (
            {'id': user.entites.first().id, 'nom_entite': user.entites.first().nom_entite,
             'type_entite': user.entites.first().type_entite}
            if hasattr(user, 'entites') and user.entites.count() == 1 else None
        ),
        'authentifie': True,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_view(request):

    username = str(request.data.get('username') or '').strip()
    password = str(request.data.get('password') or '')
    nom_agent = str(request.data.get('nom_agent') or '').strip()

    # Le nom déclaré est obligatoire.
    if not nom_agent:
        return Response(
            {
                'erreur': (
                    "Le nom et prénom de l'agent sont "
                    "obligatoires pour la traçabilité."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {
                'erreur': (
                    'Identifiant ou mot de passe incorrect, '
                    'ou compte désactivé.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Ouverture de la session Django.
    django_login(request, user)

    # Conservation de l'identité déclarée dans cette session.
    request.session['agent_nom_saisi'] = nom_agent

    return Response(_profil(user, request))


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def me(request):

    if not request.user.is_authenticated:
        return Response({'authentifie': False})

    return Response(_profil(request.user, request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):

    request.session.pop('agent_nom_saisi', None)

    django_logout(request)

    return Response({'deconnecte': True})