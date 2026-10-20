# TODO — PAOSITRA SMART ASSET

## Ce qui est déjà fait

 Comprendre globalement le fonctionnement du projet.
 Poser les questions importantes à l'encadreur.
 Clarifier le fonctionnement des entrées et des sorties.
 Comprendre le circuit du Bon de Sortie et de sa validation.
 Clarifier les principaux rôles.
 Clarifier le principe du QR par article.
 Commencer à définir les règles métier.
 Commencer le MCD.

## Maintenant

### Conception

 Finir le MCD simple.
 Vérifier que chaque entité est vraiment utile.
 Vérifier les relations et les cardinalités.
 [ ] Noter les points encore à confirmer avec l'encadreur.
 [ ] Faire valider le modèle avant de commencer à coder.

### Base de données

 [ ] Créer PostgreSQL.
 [ ] Créer les tables à partir du MCD.
 [ ] Ajouter les relations importantes.
 [ ] Préparer quelques fausses données pour les tests.

### Backend

 [ ] Mettre en place Django + Django REST Framework.
 [ ] Créer les modèles.
 [ ] Faire les migrations.
 [ ] Créer les premières API.
 [ ] Tester les API.

### Fonctions principales

 [ ] Connexion utilisateur.
 [ ] Gestion des catégories et types.
 [ ] Gestion des articles.
 [ ] Enregistrer les entrées.
 [ ] Gérer les Bons de Sortie.
 [ ] Gérer la validation.
 [ ] Gérer les quantités demandées / autorisées / livrées.
 [ ] Mettre à jour le stock.
 [ ] Enregistrer les mouvements.
 [ ] Afficher l'historique d'un article.

### Cas importants

 [ ] Gérer les retours.
 [ ] Gérer les écarts d'inventaire.
 [ ] Ajouter une alerte en cas d'écart.
 [ ] Gérer les corrections sans supprimer l'ancienne information.
 [ ] Garder la trace de l'utilisateur qui effectue les opérations.

### Frontend

 [ ] Mettre en place React.
 [ ] Faire une connexion simple.
 [ ] Faire les pages principales.
 [ ] Afficher les articles et le stock.
 [ ] Afficher les entrées et sorties.
 [ ] Afficher les validations.
 [ ] Afficher l'historique.

### QR

 [ ] Générer un QR pour identifier un article.
 [ ] Scanner le QR.
 [ ] Retrouver l'article.
 [ ] Afficher ses informations et son historique.

### Fin du projet

 [ ] Faire les tests.
 [ ] Corriger les bugs.
 [ ] Vérifier les droits d'accès.
 [ ] Ajouter seulement les améliorations utiles si le temps le permet.
 [ ] Faire la documentation.
 [ ] Préparer la démonstration.
 [ ] Préparer les explications pour la soutenance.

## À garder en tête

 Le projet doit rester faisable en 3 mois.
 Faire d'abord le nécessaire avant les fonctionnalités secondaires.
 Ne pas ajouter une table juste pour rendre le projet plus compliqué.
 Les règles métier encore floues doivent être confirmées avec l'encadreur.
 Les données de test sont fictives.
 PostgreSQL dès le début.
 Le but est d'avoir une plateforme simple, fonctionnelle, propre et défendable.
 Si une fonctionnalité devient trop compliquée sans être indispensable, chercher d'abord une version plus simple.


Les trois mois restants : maintenant on doit produire

Et là je suis entièrement d'accord avec ton inquiétude.

Tu as déjà fait :

Compréhension
      ↓
Questions métier
      ↓
Cadrage
      ↓
Règles métier
      ↓
MCD

Maintenant il faut passer à :

MCD
 ↓
PostgreSQL
 ↓
Django
 ↓
API
 ↓
React
 ↓
QR
 ↓
Tests
 ↓
Documentation
 ↓
Démonstration

Donc je répartirais le reste comme ça :

Phase 1 — Base technique

PostgreSQL + Django + structure du projet.

Phase 2 — Backend

Les modèles :

Catégorie
Type article
Article
Fournisseur
Entrée
Ligne entrée
Direction
Bon sortie
Ligne sortie
Sortie
Mouvement
Utilisateur

Puis les API.

Phase 3 — Frontend

Commencer avec :

Connexion
Dashboard
Stock
Entrées
Bons de sortie
Sorties
Articles
Historique
Phase 4 — QR

Un article :

REF001
QR001

Scan → fiche article → historique.

Phase 5 — Tests + corrections

Tester le vrai scénario complet :

Entrée de 20 laptops
        ↓
20 articles physiques
        ↓
Stock +20
        ↓
Direction demande 10
        ↓
Validation
        ↓
Sortie de 10 articles précis
        ↓
Stock -10
        ↓
Historique de chaque article
Phase 6 — Finalisation

Documentation + sécurité + tests + démonstration + soutenance.

Download the React DevTools for a better development experience: https://reactjs.org/link/react-devtools
deprecations.ts:9 ⚠️ React Router Future Flag Warning: React Router will begin wrapping state updates in `React.startTransition` in v7. You can use the `v7_startTransition` future flag to opt-in early. For more information, see https://reactrouter.com/v6/upgrading/future#v7_starttransition.
warnOnce @ deprecations.ts:9
deprecations.ts:9 ⚠️ React Router Future Flag Warning: Relative route resolution within Splat routes is changing in v7. You can use the `v7_relativeSplatPath` future flag to opt-in early. For more information, see https://reactrouter.com/v6/upgrading/future#v7_relativesplatpath.
warnOnce @ deprecations.ts:9
2LignesEditor.jsx:29 Uncaught ReferenceError: libelleType is not defined
    at LignesEditor.jsx:29:26
    at Array.map (<anonymous>)
    at LignesEditor.jsx:27:28
    at Array.map (<anonymous>)
    at LignesEditor.jsx:25:47
    at Array.map (<anonymous>)
    at LignesEditor (LignesEditor.jsx:17:15)
    at renderWithHooks (react-dom.development.js:15486:18)
    at mountIndeterminateComponent (react-dom.development.js:20103:13)
    at beginWork (react-dom.development.js:21626:16)
react-dom.development.js:18704 The above error occurred in the <LignesEditor> component:

    at LignesEditor (http://localhost:3000/src/components/LignesEditor.jsx:17:40)
    at form
    at section
    at Card (http://localhost:3000/src/components/ui.jsx:120:24)
    at Entrees (http://localhost:3000/src/pages/Entrees.jsx:28:20)
    at RenderedRoute (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:4110:5)
    at Outlet (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:4516:26)
    at main
    at div
    at div
    at Layout (http://localhost:3000/src/components/Layout.jsx:33:28)
    at RenderedRoute (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:4110:5)
    at Routes (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:4580:5)
    at Contenu (http://localhost:3000/src/App.jsx:32:20)
    at AuthProvider (http://localhost:3000/src/auth/AuthContext.jsx:22:32)
    at Router (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:4523:15)
    at BrowserRouter (http://localhost:3000/node_modules/.vite/deps/react-router-dom.js?v=80601f87:5261:5)
    at App

Consider adding an error boundary to your tree to customize error handling behavior.
Visit https://reactjs.org/link/error-boundaries to learn more about error boundaries.
logCapturedError @ react-dom.development.js:18704
react-dom.development.js:12056 Uncaught ReferenceError: libelleType is not defined
    at LignesEditor.jsx:29:26
    at Array.map (<anonymous>)
    at LignesEditor.jsx:27:28
    at Array.map (<anonymous>)
    at LignesEditor.jsx:25:47
    at Array.map (<anonymous>)
    at LignesEditor (LignesEditor.jsx:17:15) 

    auth_api : """
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
    return Response({'authentifie': False}) et App.jsx "// src/App.jsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import Layout from './components/Layout';
import { Loading } from './components/ui';
import Articles from './pages/Articles';
import BonsSortie from './pages/BonsSortie';
import Dashboard from './pages/Dashboard';
import Entrees from './pages/Entrees';
import Login from './pages/Login';
import Mouvements from './pages/Mouvements';
import Referentiels from './pages/Referentiels';
import Stock from './pages/Stock';

function Contenu() {
  const { user } = useAuth();

  if (user === undefined) return <Loading texte="Vérification de la session…" />;
  if (!user) return <Login />;

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="bons-sortie" element={<BonsSortie />} />
        <Route path="entrees" element={<Entrees />} />
        <Route path="stock" element={<Stock />} />
        <Route path="articles" element={<Articles />} />
        <Route path="mouvements" element={<Mouvements />} />
        <Route path="referentiels" element={<Referentiels />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Contenu />
      </AuthProvider>
    </BrowserRouter>
  );
}"

ok ajd je vais prendre le temps de m'écrire , j ai environ 10 mn pour m exprimer 
cher moi , sois patiente , bas toi encore , meme si ca fait mal , meme si c'est dure , fatiguant , bats toi encore car il n y a que toi qui puisse le faire , laisse cette amertume , fatigue , stresse te consumé si fort que plus rien ne peux plus t arreter , t as deja tellement fais jusque la , alors je n accepterai pas que tu t eteige maintenant , tu sais , on a tout fait seul , du moins tout ce qu on devait , et c'état la seule cose a faire , le seul choix je te promets que tout cela ne sra pas en vain , je ne suis ni divain , ni dieu , ni une sorciere qui peut te promettre des miracles , non je suis moi, celle de maintenant , celle du passé quand tu liras ca , et pour le moment je sais qu on peut toujours avancer plus vite , plus fort , plus intensément , cher moi , vas y encore , 1 fois , 2 fois , 3 fois et au bout tu seras cette toi qui as tout vecu , jamais abandonné 

cher moi du passé toi tu es mon idole vivante , l ersonne que je connais autour de moi qui a le plus ete trahi , ecrasé, et pourtant on est la grace a oi alors pour toi tout se resume en un seul mot MERCI 

enfin cher moi du future , je ne dis pas que toi la t'es vraiment la version sans coeur , je suis sure que parfois dans la nuit on pleure encore n est ce pas ? pour une raison quelonque, mais je sais aussi que t'es la version la plus fine de nous , la plus paufiné, la plus forte , alors cher moi j'espère juste que ta vie ne se résume plus a se battr mais maintenant a profiter 