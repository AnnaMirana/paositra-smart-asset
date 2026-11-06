import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import { fmtDateHeure, TYPES_MOUVEMENT } from '../lib/format';
import { useLoad } from '../lib/hooks';

const LIMITE = 300;

export default function Mouvements() {
  const [typeMouvement, setTypeMouvement] = useState('');
  const [entiteId, setEntiteId] = useState('');
  const [selectedAgent, setSelectedAgent] = useState(null);

  const { data: entites } = useLoad(() => api.list('entites'), []);
  const { data, loading, error, reload } = useLoad(
    () => api.list('mouvements', { type_mouvement: typeMouvement, entite: entiteId }),
    [typeMouvement, entiteId],
  );

  // Regroupe uniquement les mouvements portant la même référence d'opération.
  // Les anciennes lignes sans operation_ref restent affichées individuellement.
  const mouvementsGroupes = useMemo(() => {
    const groupes = new Map();

    (data || []).forEach((m) => {
      const cle = m.operation_ref || `mouvement-${m.id}`;

      if (!groupes.has(cle)) {
        groupes.set(cle, {
          ...m,
          ids: [m.id],
          cibles: [],
          quantite_totale: 0,
          nombre_articles: 0,
        });
      }

      const groupe = groupes.get(cle);
      groupe.ids.push(...(groupe.ids.includes(m.id) ? [] : [m.id]));
      if (m.cible && !groupe.cibles.includes(m.cible)) {
        groupe.cibles.push(m.cible);
      }
      groupe.quantite_totale += m.article ? 1 : Number(m.quantite || 0);
      if (m.article) groupe.nombre_articles += 1;
    });

    return Array.from(groupes.values());
  }, [data]);

  const handleAgentClick = (m) => {
    const details = m.utilisateur_details || {};
    const nomComplet =
      details.nom_complet ||
      m.utilisateur_nom_saisi ||
      [details.first_name, details.last_name].filter(Boolean).join(' ') ||
      m.utilisateur_nom ||
      'Nom non renseigné';

    setSelectedAgent({
      username: m.utilisateur_nom,
      nomComplet,
      role: details.role_libelle || m.utilisateur_role_saisi || details.role || 'Agent',
    });
  };

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
          <button type="button" className="btn" onClick={() => api.exporter('mouvements', 'excel', { type_mouvement: typeMouvement, entite: entiteId })}>Exporter Excel</button>
          <button type="button" className="btn" onClick={() => api.exporter('mouvements', 'pdf', { type_mouvement: typeMouvement, entite: entiteId })}>Exporter PDF</button>
          <button type="button" className="btn" onClick={reload}>
            Actualiser
          </button>
        </div>

        {loading && !data ? (
          <Loading />
        ) : error && !data ? (
          <ErreurChargement erreur={error} onRetry={reload} />
        ) : mouvementsGroupes.length === 0 ? (
          <Empty>Aucun mouvement.</Empty>
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Mouvement / Opération</th>
                    <th>Article / Type</th>
                    <th className="num">Quantité totale</th>
                    <th>Entité</th>
                    <th>Enregistré par</th>
                  </tr>
                </thead>
                <tbody>
                  {mouvementsGroupes.slice(0, LIMITE).map((m) => (
                    <tr key={m.operation_ref || m.id}>
                      <td>{fmtDateHeure(m.date_mouvement)}</td>
                      <td>
                        {TYPES_MOUVEMENT[m.type_mouvement] || m.type_mouvement}
                        {m.operation_ref && (
                          <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
                            {m.operation_ref}
                          </div>
                        )}
                      </td>
                      <td>
                        {m.cibles.length > 1
                          ? `${m.cibles.length} références : ${m.cibles.slice(0, 3).join(', ')}${m.cibles.length > 3 ? '…' : ''}`
                          : (m.cibles[0] || m.type_article_nom || '—')}
                      </td>
                      <td className="num">{m.quantite_totale}</td>
                      <td>{m.entite ? <Link to={`/entites/${m.entite}`}>{m.entite_nom}</Link> : '—'}</td>
                      <td>
                        <button
                          type="button"
                          onClick={() => handleAgentClick(m)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#0056b3',
                            cursor: 'pointer',
                            padding: 0,
                            fontWeight: 'bold',
                            textDecoration: 'underline',
                          }}
                        >
                          {m.utilisateur_nom_saisi || m.utilisateur_nom || '—'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {mouvementsGroupes.length > LIMITE && (
              <small>
                {LIMITE} opérations les plus récentes affichées sur {mouvementsGroupes.length}. Utilise les filtres pour affiner.
              </small>
            )}
          </>
        )}
      </Card>

      {selectedAgent && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 9999,
        }}>
          <div style={{
            backgroundColor: '#fff', padding: '24px', borderRadius: '8px', width: '380px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#1e293b', fontSize: '1.2rem' }}>
              Détails de l'Agent
            </h3>
            <div style={{ fontSize: '0.95rem', lineHeight: '1.6', color: '#334155', marginBottom: '20px' }}>
              <p><strong>Identifiant technique :</strong> {selectedAgent.username}</p>
              <p><strong>Nom & Prénom déclarés :</strong> {selectedAgent.nomComplet}</p>
              <p><strong>Rôle :</strong> {selectedAgent.role}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <button
                type="button"
                onClick={() => setSelectedAgent(null)}
                className="btn"
                style={{
                  backgroundColor: '#1e293b', color: '#fff', border: 'none',
                  padding: '8px 16px', borderRadius: '4px', cursor: 'pointer',
                }}
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
