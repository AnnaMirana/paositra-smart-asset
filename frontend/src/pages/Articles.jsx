import { useMemo, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { Alert, Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import { useLoad } from '../lib/hooks';

// Exemplaires physiques (types suivis individuellement). Lecture seule : un article naît d'une entrée.
export default function Articles() {
  const { user } = useAuth();
  const [typeId, setTypeId] = useState('');
  const [recherche, setRecherche] = useState('');

  const { data: types } = useLoad(() => api.list('types-article', { gestion_individuelle: 'true' }), []);
  const { data, loading, error, reload } = useLoad(() => api.list('articles', { type_article: typeId }), [typeId]);

  const lignes = useMemo(() => {
    const q = recherche.trim().toLowerCase();
    return (data || []).filter(
      (a) => !q || `${a.ref_article} ${a.num_serie || ''} ${a.qr_code || ''}`.toLowerCase().includes(q),
    );
  }, [data, recherche]);

  return (
    <>
      <PageHeader titre="Articles" sousTitre="Exemplaires physiques suivis individuellement (ordinateurs, imprimantes…)." />

      {(user.is_staff || user.is_superuser) && (
        <Alert type="info">
          Pour compléter une référence, un numéro de série ou un QR code, ouvre l’article dans{' '}
          <a href="/admin/inventaire/article/" target="_blank" rel="noreferrer">
            l’administration Django
          </a>
          .
        </Alert>
      )}

      <Card>
        <div className="filtres">
          <Field label="Type d’article">
            <select value={typeId} onChange={(e) => setTypeId(e.target.value)}>
              <option value="">Tous</option>
              {(types || []).map((t) => (
                <option key={t.id} value={t.id}>
                  {t.nom_type_article}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Rechercher">
            <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Référence, n° de série, QR…" />
          </Field>
        </div>

        {loading && !data ? (
          <Loading />
        ) : error && !data ? (
          <ErreurChargement erreur={error} onRetry={reload} />
        ) : lignes.length === 0 ? (
          <Empty>Aucun article.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>N° de série</th>
                  <th>QR code</th>
                  <th>Type</th>
                  <th>Marque</th>
                </tr>
              </thead>
              <tbody>
                {lignes.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <strong>{a.ref_article}</strong>
                    </td>
                    <td>{a.num_serie || '—'}</td>
                    <td>{a.qr_code || '—'}</td>
                    <td>{a.type_article_nom}</td>
                    <td>{a.marque || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}