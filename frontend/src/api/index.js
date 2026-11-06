
// Toutes les fonctions qui parlent à l'API Django, au même endroit.
// Si un endpoint change côté backend (views.py / urls.py), c'est ici qu'on l'adapte.
import { construireQuery, requete, requeteMultipart, requeteMultipartDonnees } from './client';
import { asList } from '../lib/format';

export const api = {
  // --- Authentification (inventaire/auth_api.py) ---
  me: () => requete('GET', '/auth/me/'),

  // Transmission du nom de l'agent déclaré à la connexion
  login: (username, password, nomAgent) =>
    requete('POST', '/auth/login/', {
      username,
      password,
      nom_agent: nomAgent,
    }),

  logout: () => requete('POST', '/auth/logout/'),

  // --- Lecture / création génériques ---
  // Ressources : categories, fournisseurs, entites, types-article, articles, entrees,
  //              bons-sortie, lignes-bsortie, interventions, sorties, mouvements
  list: (ressource, params) =>
    requete('GET', `/${ressource}/${construireQuery(params)}`).then(asList),

  get: (ressource, id) => requete('GET', `/${ressource}/${id}/`),

  create: (ressource, donnees) =>
    requete('POST', `/${ressource}/`, donnees),

  update: (ressource, id, donnees) =>
    requete('PATCH', `/${ressource}/${id}/`, donnees),

  // --- Stock ---
  // { quantite_stock, quantite_reservee, stock_disponible_pour_autorisation, ... }
  stock: (typeId) =>
    requete('GET', `/types-article/${typeId}/stock/`),

  // --- Entrées ---
  ajouterLigneEntree: (entreeId, donnees) =>
    requete('POST', `/entrees/${entreeId}/ajouter_ligne/`, donnees),

  // --- Workflow du bon de sortie ---
  ajouterLigneBon: (bonId, donnees) =>
    requete('POST', `/bons-sortie/${bonId}/ajouter_ligne/`, donnees),

  soumettre: (bonId) =>
    requete('POST', `/bons-sortie/${bonId}/soumettre/`),

  autoriser: (ligneId, quantite, motif) =>
    requete(
      'POST',
      `/lignes-bsortie/${ligneId}/autoriser/`,
      { quantite, motif }
    ),

  valider: (ligneId, quantite, motif) =>
    requete(
      'POST',
      `/lignes-bsortie/${ligneId}/valider/`,
      { quantite, motif }
    ),

  effectuerSortie: (donnees, preuve) =>
    requeteMultipartDonnees('POST', '/sorties/effectuer/', donnees, preuve, 'document_livraison'),

  televerserDocumentBon: (id, fichier) =>
    requeteMultipart('POST', `/bons-sortie/${id}/televerser-document/`, fichier, 'document_fichier'),

  televerserDocumentEntree: (id, fichier) =>
    requeteMultipart('POST', `/entrees/${id}/televerser-document/`, fichier, 'document_fichier'),

  televerserPreuveSortie: (id, fichier) =>
    requeteMultipart('POST', `/sorties/${id}/televerser-preuve/`, fichier, 'document_livraison'),

  exporter: (ressource, format = 'excel', params = {}) => {
    const query = construireQuery(params);
    window.open(`/api/${ressource}/export-${format}/${query}`, '_blank', 'noopener,noreferrer');
  },
};
