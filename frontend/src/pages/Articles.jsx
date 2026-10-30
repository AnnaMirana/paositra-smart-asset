import { useMemo, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { Alert, Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import { fmtDate } from '../lib/format';
import { useLoad } from '../lib/hooks';

// Exemplaires physiques (types suivis individuellement). Lecture seule : un article naît d'une entrée.
export default function Articles() {
  const { user } = useAuth();
  const [typeId, setTypeId] = useState('');
  const [recherche, setRecherche] = useState('');

  // États pour la modale d'historique de l'article sélectionné et le filtre par année
  const [articleSelectionne, setArticleSelectionne] = useState(null);
  const [historiqueArticle, setHistoriqueArticle] = useState([]);
  const [loadingHistorique, setLoadingHistorique] = useState(false);
  const [anneeFiltre, setAnneeFiltre] = useState('toutes'); // 'toutes' ou une année spécifique (ex: '2026')

  const { data: types } = useLoad(() => api.list('types-article', { gestion_individuelle: 'true' }), []);
  const { data, loading, error, reload } = useLoad(() => api.list('articles', { type_article: typeId }), [typeId]);

  const lignes = useMemo(() => {
    const q = recherche.trim().toLowerCase();
    return (data || []).filter(
      (a) => !q || `${a.ref_article} ${a.num_serie || ''} ${a.qr_code || ''}`.toLowerCase().includes(q),
    );
  }, [data, recherche]);

  // Fonction pour charger l'historique et les mouvements de cet article précis
  async function ouvrirHistoriqueArticle(article) {
    setArticleSelectionne(article);
    setAnneeFiltre('toutes'); // Réinitialiser le filtre par année à l'ouverture
    setLoadingHistorique(true);
    try {
      const tousMouvements = await api.list('mouvements');
      const mouvementsArticle = (tousMouvements || []).filter(
        (m) => String(m.article) === String(article.id)
      );
      setHistoriqueArticle(mouvementsArticle);
    } catch (err) {
      alert("Erreur lors du chargement de l'historique : " + err.message);
      setHistoriqueArticle([]);
    } finally {
      setLoadingHistorique(false);
    }
  }

  // Extraire les années disponibles dans l'historique de l'article pour alimenter le sélecteur
  const anneesDisponibles = useMemo(() => {
    const anneesSet = new Set();
    historiqueArticle.forEach(m => {
      if (m.date_mouvement) {
        const annee = m.date_mouvement.slice(0, 4);
        anneesSet.add(annee);
      }
    });
    return Array.from(anneesSet).sort().reverse();
  }, [historiqueArticle]);

  // Filtrer l'historique selon l'année sélectionnée
  const historiqueFiltre = useMemo(() => {
    if (anneeFiltre === 'toutes') return historiqueArticle;
    return historiqueArticle.filter(m => m.date_mouvement && m.date_mouvement.startsWith(anneeFiltre));
  }, [historiqueArticle, anneeFiltre]);

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

      {/* MODALE DE SUIVI / HISTORIQUE DE L'ARTICLE AVEC FILTRE PAR ANNÉE */}
      {articleSelectionne && (
        <div className="modal-backdrop" style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="card" style={{ background: '#fff', padding: '2rem', borderRadius: '8px', width: '90%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>Historique de l'article : {articleSelectionne.ref_article}</h2>
              
              {/* Sélecteur d'année pour le filtrage des archives */}
              {anneesDisponibles.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>Année :</label>
                  <select 
                    value={anneeFiltre} 
                    onChange={(e) => setAnneeFiltre(e.target.value)}
                    style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  >
                    <option value="toutes">Toutes les années</option>
                    {anneesDisponibles.map(annee => (
                      <option key={annee} value={annee}>{annee}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <hr style={{ margin: '1rem 0' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              <p><strong>Type d'article :</strong> {articleSelectionne.type_article_nom || '—'}</p>
              <p><strong>Marque :</strong> {articleSelectionne.marque || '—'}</p>
              <p><strong>N° de série :</strong> {articleSelectionne.num_serie || '—'}</p>
              <p><strong>Code QR :</strong> {articleSelectionne.qr_code || '—'}</p>
            </div>

            <h3 style={{ marginTop: '1.5rem' }}>Mouvements et traçabilité</h3>
            {loadingHistorique ? (
              <p style={{ marginTop: '1rem' }}>Chargement de l'historique...</p>
            ) : historiqueArticle.length === 0 ? (
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', marginTop: '0.5rem' }}>
                <p style={{ fontSize: '0.9rem', color: '#0369a1', margin: 0 }}>
                  📦 Cet article est actuellement <strong>en stock</strong> (aucun mouvement de sortie enregistré).
                </p>
              </div>
            ) : historiqueFiltre.length === 0 ? (
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '6px', marginTop: '0.5rem' }}>
                <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>
                  Aucun mouvement enregistré pour l'année sélectionnée ({anneeFiltre}).
                </p>
              </div>
            ) : (
              <div className="table-wrap" style={{ marginTop: '0.5rem', maxHeight: '250px', overflowY: 'auto' }}>
                <table className="table" style={{ width: '100%', fontSize: '0.85rem' }}>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type de mouvement</th>
                      <th>Entité bénéficiaire</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historiqueFiltre.map((m) => (
                      <tr key={m.id}>
                        <td>{fmtDate(m.date_mouvement)}</td>
                        <td><span className="badge">{m.type_mouvement || 'Sortie'}</span></td>
                        <td><strong>{m.entite_nom || '—'}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ marginTop: '2rem', textAlign: 'right' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setArticleSelectionne(null)}>
                Fermer
              </button>
            </div>
          </div>
        </div>
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
                      <button
                        type="button"
                        onClick={() => ouvrirHistoriqueArticle(a)}
                        style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', fontWeight: 'bold', padding: 0, textDecoration: 'underline' }}
                        title="Cliquer pour voir l'historique et l'entité de cet article"
                      >
                        {a.ref_article}
                      </button>
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