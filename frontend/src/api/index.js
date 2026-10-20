// Toutes les fonctions qui parlent à l'API Django, au même endroit.
// Si un endpoint change côté backend (views.py / urls.py), c'est ici qu'on l'adapte.
import { construireQuery, requete } from './client';
import { asList } from '../lib/format';

export const api = {
  // --- Authentification (inventaire/auth_api.py) ---
  me: () => requete('GET', '/auth/me/'),
  login: (username, password) => requete('POST', '/auth/login/', { username, password }),
  logout: () => requete('POST', '/auth/logout/'),

  // --- Lecture / création génériques ---
  // Ressources : categories, fournisseurs, entites, types-article, articles, entrees,
  //              bons-sortie, lignes-bsortie, interventions, sorties, mouvements
  list: (ressource, params) => requete('GET', `/${ressource}/${construireQuery(params)}`).then(asList),
  get: (ressource, id) => requete('GET', `/${ressource}/${id}/`),
  create: (ressource, donnees) => requete('POST', `/${ressource}/`, donnees),

  // --- Stock ---
  // { quantite_stock, quantite_reservee, stock_disponible_pour_autorisation, ... }
  stock: (typeId) => requete('GET', `/types-article/${typeId}/stock/`),

  // --- Entrées ---
  ajouterLigneEntree: (entreeId, donnees) => requete('POST', `/entrees/${entreeId}/ajouter_ligne/`, donnees),

  // --- Workflow du bon de sortie ---
  ajouterLigneBon: (bonId, donnees) => requete('POST', `/bons-sortie/${bonId}/ajouter_ligne/`, donnees),
  soumettre: (bonId) => requete('POST', `/bons-sortie/${bonId}/soumettre/`),
  autoriser: (ligneId, quantite, motif) =>
    requete('POST', `/lignes-bsortie/${ligneId}/autoriser/`, { quantite, motif }),
  valider: (ligneId, quantite, motif) =>
    requete('POST', `/lignes-bsortie/${ligneId}/valider/`, { quantite, motif }),
  effectuerSortie: (donnees) => requete('POST', '/sorties/effectuer/', donnees),
};