import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import { fmtDateHeure, TYPES_MOUVEMENT } from '../lib/format';
import { useLoad } from '../lib/hooks';

const LIMITE = 300;

// Traçabilité : chaque entrée, sortie, etc. avec qui, quand, quoi et pour quelle entité.
export default function Mouvements() {
  const [typeMouvement, setTypeMouvement] = useState('');
  const [entiteId, setEntiteId] = useState('');

  const { data: entites } = useLoad(() => api.list('entites'), []);
  const { data, loading, error, reload } = useLoad(
    () => api.list('mouvements', { type_mouvement: typeMouvement, entite: entiteId }),
    [typeMouvement, entiteId],
  );

  return (
    <>
      <PageHeader titre="Mouvements" sousTitre="Historique complet : jamais supprimé, jamais modifié à la main." />
      <Card>
        <div className="filtres">
          <Field label="Type de mouvement">
            <select value={typeMouvement} onChange={(e) => setTypeMouvement(e.target.value)}>
              <option value="">Tous</option>
              {Object.entries(TYPES_MOUVEMENT).map(([valeur, libelle]) => (
                <option key={valeur} value={valeur}>
                  {libelle}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Entité concernée">
            <select value={entiteId} onChange={(e) => setEntiteId(e.target.value)}>
              <option value="">Toutes</option>
              {(entites || []).map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nom_entite}
                </option>
              ))}
            </select>
          </Field>
          <button type="button" className="btn" onClick={reload}>
            Actualiser
          </button>
        </div>

        {loading && !data ? (
          <Loading />
        ) : error && !data ? (
          <ErreurChargement erreur={error} onRetry={reload} />
        ) : data.length === 0 ? (
          <Empty>Aucun mouvement.</Empty>
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Mouvement</th>
                    <th>Article / Type</th>
                    <th className="num">Quantité</th>
                    <th>Entité</th>
                    <th>Enregistré par</th>
                  </tr>
                </thead>
                <tbody>
                  {data.slice(0, LIMITE).map((m) => (
                    <tr key={m.id}>
                      <td>{fmtDateHeure(m.date_mouvement)}</td>
                      <td>{TYPES_MOUVEMENT[m.type_mouvement] || m.type_mouvement}</td>
                      <td>{m.article ? m.cible : m.type_article_nom}</td>
                      <td className="num">{m.article ? 1 : m.quantite}</td>
                      <td>{m.entite ? <Link to={`/entites/${m.entite}`}>{m.entite_nom}</Link> : '—'}</td>
                      <td>{m.utilisateur_nom}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.length > LIMITE && (
              <small>
                {LIMITE} mouvements les plus récents affichés sur {data.length}. Utilise les filtres pour affiner.
              </small>
            )}
          </>
        )}
      </Card>
    </>
  );
}