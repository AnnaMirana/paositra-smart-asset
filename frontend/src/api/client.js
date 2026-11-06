// client.js (Version corrigée)
const BASE = '/api';

export class ApiError extends Error {
  constructor(status, data) {
    super('');
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.message = messageDepuis(status, data);
  }
}

let surNonAutorise = null;
export function definirGestionnaireNonAutorise(fn) {
  surNonAutorise = fn;
}

function lireCookie(nom) {
  const trouve = document.cookie.split('; ').find((c) => c.startsWith(nom + '='));
  return trouve ? decodeURIComponent(trouve.split('=').slice(1).join('=')) : '';
}

export function construireQuery(params = {}) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([cle, valeur]) => {
    if (valeur !== undefined && valeur !== null && valeur !== '') p.append(cle, valeur);
  });
  const texte = p.toString();
  return texte ? `?${texte}` : '';
}

const LIBELLES_CHAMPS = {
  nom_categorie: 'Nom de la catégorie',
  nom_type_article: "Nom du type d'article",
  nom_fournisseur: 'Nom du fournisseur',
  nom_entite: "Nom de l'entité",
  sigle_entite: 'Sigle',
  type_entite: "Type d'entité",
  categorie: 'Catégorie',
  reference_bs: 'Référence',
  ref_entree: 'Référence',
  date_bs: 'Date',
  date_entree: 'Date',
  date_sortie: 'Date de sortie',
  entite: 'Entité',
  fournisseur: 'Fournisseur',
  origine: 'Origine',
  type_article: "Type d'article",
  quantite: 'Quantité',
  quantite_demandee: 'Quantité demandée',
  motif: 'Motif',
};

function aplatir(donnee) {
  if (donnee === null || donnee === undefined) return '';
  if (typeof donnee === 'string') return donnee;
  if (Array.isArray(donnee)) return donnee.map(aplatir).filter(Boolean).join(' ');
  if (typeof donnee === 'object') {
    if (donnee.erreur) return aplatir(donnee.erreur);
    if (donnee.detail) return aplatir(donnee.detail);
    return Object.entries(donnee)
      .map(([cle, valeur]) => {
        const txt = aplatir(valeur);
        if (cle === 'non_field_errors') return txt;
        return `${LIBELLES_CHAMPS[cle] || cle} : ${txt}`;
      })
      .join(' ');
  }
  return String(donnee);
}

function messageDepuis(status, donnee) {
  const texte = aplatir(donnee);
  if (texte) return texte;
  if (status === 0) {
    return 'Impossible de joindre le serveur. Vérifie que le backend Django tourne.';
  }
  if (status === 404) return 'Élément introuvable.';
  if (status >= 500) return `Erreur interne du serveur (${status}).`;
  return `Erreur ${status}`;
}

export function messageErreur(erreur) {
  if (!erreur) return '';
  return erreur.message || String(erreur);
}

export async function requete(methode, chemin, corps) {
  const options = {
    method: methode,
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  };
  if (corps !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(corps);
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(methode)) {
    options.headers['X-CSRFToken'] = lireCookie('csrftoken');
  }

  let reponse;
  try {
    reponse = await fetch(BASE + chemin, options);
  } catch {
    throw new ApiError(0, null);
  }

  let donnee = null;
  const texte = await reponse.text();
  if (texte) {
    try {
      donnee = JSON.parse(texte);
    } catch {
      donnee = null;
    }
  }

  if (!reponse.ok) {
    if (reponse.status === 403 && donnee && donnee.detail && !donnee.erreur && surNonAutorise) {
      surNonAutorise();
    }
    throw new ApiError(reponse.status, donnee);
  }
  return donnee;
}

// Envoi de fichiers : ne surtout pas fixer Content-Type, le navigateur ajoute la boundary multipart.
export async function requeteMultipart(methode, chemin, fichier, nomChamp) {
  const form = new FormData();
  form.append(nomChamp, fichier);
  const options = { method: methode, credentials: 'same-origin', headers: { Accept: 'application/json' }, body: form };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(methode)) options.headers['X-CSRFToken'] = lireCookie('csrftoken');
  let reponse;
  try { reponse = await fetch(BASE + chemin, options); } catch { throw new ApiError(0, null); }
  const texte = await reponse.text();
  let donnee = null;
  if (texte) { try { donnee = JSON.parse(texte); } catch { donnee = null; } }
  if (!reponse.ok) throw new ApiError(reponse.status, donnee);
  return donnee;
}


export async function requeteMultipartDonnees(methode, chemin, donnees, fichier, nomChamp) {
  const form = new FormData();
  Object.entries(donnees || {}).forEach(([cle, valeur]) => {
    if (valeur !== undefined && valeur !== null) form.append(cle, typeof valeur === 'object' ? JSON.stringify(valeur) : String(valeur));
  });
  form.append(nomChamp, fichier);
  const options = { method: methode, credentials: 'same-origin', headers: { Accept: 'application/json' }, body: form };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(methode)) options.headers['X-CSRFToken'] = lireCookie('csrftoken');
  let reponse;
  try { reponse = await fetch(BASE + chemin, options); } catch { throw new ApiError(0, null); }
  const texte = await reponse.text();
  let donnee = null;
  if (texte) { try { donnee = JSON.parse(texte); } catch { donnee = null; } }
  if (!reponse.ok) throw new ApiError(reponse.status, donnee);
  return donnee;
}
