"""
Authentification pour le frontend React (Mois 2).

Principe : connexion par SESSION Django (cookie), la même que l'admin et l'API
navigable. React n'a donc aucun jeton à stocker ; il envoie le cookie de session
et l'en-tête X-CSRFToken (lu dans le cookie csrftoken) pour les requêtes qui
modifient des données.

  GET  /api/auth/me/      -> qui suis-je ? (profil + rôle) ; pose aussi le cookie CSRF
  POST /api/auth/login/   -> {username, password}
  POST /api/auth/logout/
"""
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


def _profil(user):
    return {
        'authentifie': True,
        'id': user.id,
        'username': user.username,
        'nom_complet': user.get_full_name() or user.username,
        'role': user.role,
        'role_libelle': user.get_role_display() if user.role else '',
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'entites': list(user.entites.values_list('id', flat=True)),
    }


@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    if request.user.is_authenticated:
        return Response(_profil(request.user))
    return Response({'authentifie': False})


@api_view(['POST'])
@authentication_classes([])          # pas de vérification CSRF pour la connexion elle-même
@permission_classes([AllowAny])
def login_view(request):
    username = str(request.data.get('username', '')).strip()
    password = str(request.data.get('password', ''))
    # authenticate() refuse aussi les comptes désactivés (actif=False -> is_active=False).
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'erreur': 'Identifiant ou mot de passe incorrect, ou compte désactivé.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    login(request, user)
    return Response(_profil(user))


@api_view(['POST'])
@authentication_classes([])  # Désactive la vérification CSRF / Session de DRF
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response({'authentifie': False})