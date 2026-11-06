// Qui voit quel bouton ?
//
// IMPORTANT : ces fonctions ne servent qu'à ne pas afficher des boutons inutiles.
// La vraie vérification est faite par le serveur (backend/inventaire/services.py, constantes ROLES_*) :
// même si quelqu'un contournait l'interface, le serveur refuserait (réponse 403).
// Si tu changes un rôle autorisé dans services.py, change-le aussi ici.

const a = (utilisateur, roles) =>
    Boolean(utilisateur && (utilisateur.is_superuser || utilisateur.role === 'admin' || roles.includes(utilisateur.role)));

export const ROLES_SOUMISSION = ['demandeur', 'agent_direction'];
export const ROLES_AUTORISATION = ['agent_dsid'];
export const ROLES_VALIDATION = ['agent_validation'];
export const ROLES_SORTIE = ['agent_came'];

export const peutAutoriser = (u) => a(u, ROLES_AUTORISATION);
export const peutValider = (u) => a(u, ROLES_VALIDATION);
export const peutSortir = (u) => a(u, ROLES_SORTIE);

// Rôle capable de soumettre un bon (sans tenir compte de qui l'a créé).
export const peutSoumettreRole = (u) => a(u, ROLES_SOUMISSION);

// Soumettre un bon précis : seulement son créateur (ou un super-utilisateur).
export const peutSoumettre = (u, bon) =>
    Boolean(u && bon && peutSoumettreRole(u) && (u.is_superuser || bon.utilisateur === u.id));

// L'auditeur consulte seulement : on lui cache les boutons de création.
export const peutEcrire = (u) => Boolean(u && (u.is_superuser || u.role === 'admin' || u.role === 'agent_came'));