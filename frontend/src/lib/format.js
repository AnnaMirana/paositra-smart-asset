// Libellés affichés à l'écran (les valeurs techniques viennent de models.py : choices).

export const STATUTS_BS = {
    brouillon: 'Brouillon' ,
    en_attente_autorisation: "En attente d'autorisation",
    en_attente_validation: 'En attente de validation',
    valide: 'Validé',
    refuse: 'Refusé',
    sorti: 'Sorti',
};

export const ETATS_LIGNE = {
    demandee: 'Demandée',
    autorisee: 'Autorisée',
    refusee: 'Refusée',
    validee: 'Validée',
    rejetee: 'Rejetée',
    sortie: 'Sortie',
};

export const TYPES_MOUVEMENT = {
    entree: 'Entrée en stock',
    sortie: 'Sortie',
    retour: 'Retour',
    controle_retour: 'Contrôle de retour',
    reintegration: 'Réintégration',
    mise_hors_service: 'Mise hors service',
    perte: 'Perte déclarée',
    correction: 'Correction',
};

export const ORIGINES = { achat: 'Achat', don: 'Don' };
export const TYPES_ENTITE = { direction: 'Direction', agence: 'Agence', depot: 'Dépôt' };
export const ROLES_INTERVENTION = { autorisation: 'Autorisation DSID', validation: 'Validation DCA' };

// L'API renvoie une liste simple ; on accepte aussi un format paginé ({results: [...]}).
export const asList = (donnee) => (Array.isArray(donnee) ? donnee : donnee?.results ?? []);

const deuxChiffres = (n) => String(n).padStart(2, '0');

// Date du jour au format AAAA-MM-JJ (heure locale, pas UTC).
export function today() {
  const d = new Date();
  return `${d.getFullYear()}-${deuxChiffres(d.getMonth() + 1)}-${deuxChiffres(d.getDate())}`;
}

export function fmtDate(texte) {
  if (!texte) return '—';
  const [a, m, j] = String(texte).slice(0, 10).split('-');
  return a && m && j ? `${j}/${m}/${a}` : String(texte);
}

export function fmtDateHeure(texte) {
  if (!texte) return '—';
  const d = new Date(texte);
  if (Number.isNaN(d.getTime())) return String(texte);
  return `${deuxChiffres(d.getDate())}/${deuxChiffres(d.getMonth() + 1)}/${d.getFullYear()} ${deuxChiffres(
    d.getHours(),
  )}:${deuxChiffres(d.getMinutes())}`;
}

// « Catégorie — Type (marque) » : libellé d'un type d'article dans les listes déroulantes.
export function libelleType(t) {
  return `${t.categorie_nom} — ${t.nom_type_article}${t.marque ? ` (${t.marque})` : ''}`;
}