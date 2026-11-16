
// Toutes les fonctions qui communiquent avec l'API Django.
import {
  construireQuery,
  requete,
  requeteMultipart,
  requeteMultipartDonnees,
} from './client';

import { asList } from '../lib/format';

export const api = {
  // --- Authentification ---
  me: () => requete('GET', '/auth/me/'),

  // Connexion avec le nom complet et le mot de passe uniquement.
  login: (nom, password) =>
    requete('POST', '/auth/login/', {
      nom,
      password,
    }),

  logout: () => requete('POST', '/auth/logout/'),

  changerMotDePasse: (donnees) =>
    requete('POST', '/auth/changer-mot-de-passe/', donnees),

  // --- Lecture / création génériques ---
  list: (ressource, params) =>
    requete(
      'GET',
      `/${ressource}/${construireQuery(params)}`
    ).then(asList),

  get: (ressource, id) =>
    requete('GET', `/${ressource}/${id}/`),

  create: (ressource, donnees) =>
    requete('POST', `/${ressource}/`, donnees),

  update: (ressource, id, donnees) =>
    requete('PATCH', `/${ressource}/${id}/`, donnees),

  renvoyerMotDePasse: (id) =>
    requete(
      'POST',
      `/utilisateurs/${id}/renvoyer-mot-de-passe/`
    ),

  // --- Stock ---
  stock: (typeId) =>
    requete('GET', `/types-article/${typeId}/stock/`),

  // --- Entrées ---
  ajouterLigneEntree: (entreeId, donnees) =>
    requete(
      'POST',
      `/entrees/${entreeId}/ajouter_ligne/`,
      donnees
    ),

  // --- Workflow du bon de sortie ---
  ajouterLigneBon: (bonId, donnees) =>
    requete(
      'POST',
      `/bons-sortie/${bonId}/ajouter_ligne/`,
      donnees
    ),

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
    requeteMultipartDonnees(
      'POST',
      '/sorties/effectuer/',
      donnees,
      preuve,
      'document_livraison'
    ),

  televerserDocumentBon: (id, fichier) =>
    requeteMultipart(
      'POST',
      `/bons-sortie/${id}/televerser-document/`,
      fichier,
      'document_fichier'
    ),

  televerserDocumentEntree: (id, fichier) =>
    requeteMultipart(
      'POST',
      `/entrees/${id}/televerser-document/`,
      fichier,
      'document_fichier'
    ),

  televerserPreuveSortie: (id, fichier) =>
    requeteMultipart(
      'POST',
      `/sorties/${id}/televerser-preuve/`,
      fichier,
      'document_livraison'
    ),

  exporter: (ressource, format = 'excel', params = {}) => {
    const query = construireQuery(params);

    window.open(
      `/api/${ressource}/export-${format}/${query}`,
      '_blank',
      'noopener,noreferrer'
    );
  },
};
