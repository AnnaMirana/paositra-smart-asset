from django.http import JsonResponse

class ForcerChangementMotDePasseMiddleware:
    """
    Un compte en première connexion ne peut utiliser que /auth/me/,
    /auth/logout/ et /auth/changer-mot-de-passe/ tant que le mot de passe
    temporaire n'a pas été remplacé.
    """
    ROUTES_AUTORISEES = (
        "/api/auth/me/",
        "/api/auth/logout/",
        "/api/auth/changer-mot-de-passe/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            request.path.startswith("/api/")
            and user is not None
            and user.is_authenticated
            and getattr(user, "doit_changer_mot_de_passe", False)
            and request.path not in self.ROUTES_AUTORISEES
        ):
            return JsonResponse(
                {"code": "password_change_required",
                 "erreur": "Vous devez changer votre mot de passe avant de continuer."},
                status=403,
            )
        return self.get_response(request)
