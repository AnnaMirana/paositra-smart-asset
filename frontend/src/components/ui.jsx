import { ETATS_LIGNE, STATUTS_BS } from '../lib/format';

// Petits composants réutilisés partout. Le style est dans src/styles.css.

export function Badge({ ton = 'gris', children }) {
  return <span className={`badge badge-${ton}`}>{children}</span>;
}

const TON_STATUT = {
  brouillon: 'gris',
  en_attente_autorisation: 'jaune',
  en_attente_validation: 'bleu',
  valide: 'vert',
  refuse: 'rouge',
  sorti: 'marine',
};
const TON_ETAT = {
  demandee: 'gris',
  autorisee: 'jaune',
  refusee: 'rouge',
  validee: 'vert',
  rejetee: 'rouge',
  sortie: 'marine',
};

export const StatutBadge = ({ statut }) => <Badge ton={TON_STATUT[statut] || 'gris'}>{STATUTS_BS[statut] || statut}</Badge>;
export const EtatBadge = ({ etat }) => <Badge ton={TON_ETAT[etat] || 'gris'}>{ETATS_LIGNE[etat] || etat}</Badge>;

export function Alert({ type = 'erreur', children, onClose }) {
  if (!children) return null;
  return (
    <div className={`alert alert-${type}`} role={type === 'erreur' ? 'alert' : 'status'}>
      <div>{children}</div>
      {onClose && (
        <button type="button" className="alert-close" onClick={onClose} aria-label="Fermer">
          ✕
        </button>
      )}
    </div>
  );
}

export function Loading({ texte = 'Chargement…' }) {
  return <div className="loading">{texte}</div>;
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

export function PageHeader({ titre, sousTitre, children }) {
  return (
    <div className="page-header">
      <div>
        <h1>{titre}</h1>
        {sousTitre && <p className="sous-titre">{sousTitre}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  );
}

export function Card({ titre, actions, children, className = '' }) {
  return (
    <section className={`card ${className}`}>
      {(titre || actions) && (
        <div className="card-head">
          {titre && <h2>{titre}</h2>}
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function Field({ label, aide, children, className = '' }) {
  return (
    <label className={`field ${className}`}>
      <span className="field-label">{label}</span>
      {children}
      {aide && <small>{aide}</small>}
    </label>
  );
}

// Affiche l'écran d'erreur de chargement avec un bouton « Réessayer ».
export function ErreurChargement({ erreur, onRetry }) {
  return (
    <Alert type="erreur">
      {erreur?.message || 'Erreur de chargement.'}{' '}
      {onRetry && (
        <button type="button" className="btn btn-sm" onClick={onRetry}>
          Réessayer
        </button>
      )}
    </Alert>
  );
}