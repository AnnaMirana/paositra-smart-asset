// src/pages/Entrees.jsx
import { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { Alert, Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import LignesEditor from '../components/LignesEditor';
import { fmtDate, ORIGINES } from '../lib/format';
import { useLoad } from '../lib/hooks';
import { peutEcrire } from '../lib/roles';

export default function Entrees() {
  const { user } = useAuth();
  const [nouveauMode, setNouveauMode] = useState(false);
  const [refEntree, setRefEntree] = useState('');
  const [fournisseurId, setFournisseurId] = useState('');
  const [origine, setOrigine] = useState('achat');
  const [documentEntree, setDocumentEntree] = useState(null);
  const [lignes, setLignes] = useState([{ type_article: '', quantite: '' }]);
  const [erreur, setErreur] = useState('');

  // États pour la modale de détail et la liste des articles individuels d'une ligne
  const [entreeSelectionnee, setEntreeSelectionnee] = useState(null);
  const [articlesModal, setArticlesModal] = useState(null); // { titreType, articles: [] }
  const [loadingArticles, setLoadingArticles] = useState(false);

  const { data: fournisseurs } = useLoad(() => api.list('fournisseurs'), []);
  const { data: types } = useLoad(() => api.list('types-article'), []);
  const { data: entrees, loading, error, reload } = useLoad(() => api.list('entrees'), []);

  function ouvrirDetailEntree(entree) {
    setEntreeSelectionnee(entree);
    setArticlesModal(null);
  }

  // Fonction pour récupérer et afficher les articles individuels de cette ligne d'entrée spécifique
  async function voirArticlesLigne(ligneEntreeId, nomType) {
    setLoadingArticles(true);
    try {
      const tousArticles = await api.list('articles');

      // On filtre les articles rattachés exactement à cette ligne d'entrée
      const articlesFiltres = (tousArticles || []).filter(a => {
        return String(a.ligne_entree) === String(ligneEntreeId);
      });

      setArticlesModal({
        titre: nomType,
        articles: articlesFiltres
      });
    } catch (err) {
      alert("Erreur lors du chargement des articles : " + err.message);
    } finally {
      setLoadingArticles(false);
    }
  }

  async function enregistrerEntree(e) {
    e.preventDefault();
    setErreur('');
    try {
      if (!documentEntree) throw new Error('Le document justificatif de l’entrée est obligatoire.');
      const entree = await api.create('entrees', {
        ref_entree: refEntree.trim(),
        date_entree: new Date().toISOString().slice(0, 10),
        origine,
        fournisseur: fournisseurId,
      });
      await api.televerserDocumentEntree(entree.id, documentEntree);
      for (const l of lignes) {
        if (l.type_article && l.quantite) {
          await api.ajouterLigneEntree(entree.id, {
            type_article: l.type_article,
            quantite: parseInt(l.quantite, 10),
          });
        }
      }
      setNouveauMode(false);
      setRefEntree('');
      setDocumentEntree(null);
      setLignes([{ type_article: '', quantite: '' }]);
      reload();
    } catch (err) {
      setErreur(err.message);
      reload();
    }
  }

  if (loading && !entrees) return <Loading />;
  if (error && !entrees) return <ErreurChargement erreur={error} onRetry={reload} />;

  return (
    <>
      <PageHeader titre="Entrées en Stock" sousTitre="Enregistrement des approvisionnements et dons.">
        <button type="button" className="btn" onClick={() => api.exporter('entrees', 'excel')}>Excel</button>
        <button type="button" className="btn" onClick={() => api.exporter('entrees', 'pdf')}>PDF</button>
        {peutEcrire(user) && (
          <button type="button" className="btn btn-primary" onClick={() => setNouveauMode(!nouveauMode)}>
            {nouveauMode ? 'Fermer' : '+ Nouvelle entrée'}
          </button>
        )}
      </PageHeader>

      {/* MODALE DE DÉTAIL DE L'ENTRÉE */}
      {entreeSelectionnee && (
        <div className="modal-backdrop" style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="card" style={{ background: '#fff', padding: '2rem', borderRadius: '8px', width: '90%', maxWidth: '850px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2>Détail de l'Entrée : {entreeSelectionnee.ref_entree}</h2>
            <hr style={{ margin: '1rem 0' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <p><strong>Date d'arrivée :</strong> {fmtDate(entreeSelectionnee.date_entree)}</p>
              <p><strong>Origine :</strong> {ORIGINES[entreeSelectionnee.origine] || entreeSelectionnee.origine}</p>
              <p><strong>Fournisseur :</strong> {entreeSelectionnee.fournisseur_nom || '—'}</p>
              <p><strong>Enregistré par :</strong> {entreeSelectionnee.utilisateur_nom || '—'}</p>
            </div>

            <div style={{ margin: '1rem 0' }}>
              <strong>Document justificatif CAME : </strong>
              {entreeSelectionnee.document_fichier_url ? <a href={entreeSelectionnee.document_fichier_url} target="_blank" rel="noreferrer">Consulter le document</a> : <span>Non déposé</span>}
              {(user?.role === 'agent_came' || user?.role === 'admin' || user?.is_superuser) && (
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={async (e) => {
                  const fichier = e.target.files?.[0]; if (!fichier) return;
                  try { const maj = await api.televerserDocumentEntree(entreeSelectionnee.id, fichier); setEntreeSelectionnee(maj); reload(); }
                  catch (err) { alert('Téléversement impossible : ' + err.message); }
                  e.target.value = '';
                }} />
              )}
            </div>

            <h3 style={{ marginTop: '1.5rem' }}>Contenu du lot (Cliquez sur une quantité pour voir les articles)</h3>
            {(!entreeSelectionnee.lignes || entreeSelectionnee.lignes.length === 0) ? (
              <p>Aucune ligne enregistrée pour cette entrée.</p>
            ) : (
              <table className="table" style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.9rem' }}>
                <thead>
                  <tr>
                    <th>Type d'article</th>
                    <th>Quantité (Cliquer pour voir les exemplaires)</th>
                  </tr>
                </thead>
                <tbody>
                  {entreeSelectionnee.lignes.map((l, index) => (
                    <tr key={index}>
                      <td><strong>{l.type_article}</strong></td>
                      <td>
                        <button
                          type="button"
                          onClick={() => voirArticlesLigne(l.id, l.type_article)}
                          style={{ background: '#e0f2fe', border: '1px solid #bae6fd', color: '#0369a1', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                          title="Cliquer pour afficher la liste des articles individuels"
                        >
                          {l.quantite} unité(s) 🔍
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {/* SOUS-SECTION : LISTE DES ARTICLES INDIVIDUELS DE LA LIGNE SÉLECTIONNÉE */}
            {loadingArticles && <p style={{ marginTop: '1rem' }}>Chargement des articles individuels...</p>}

            {articlesModal && (
              <div style={{ marginTop: '2rem', background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <h4>Exemplaires individuels pour : {articlesModal.titre} ({articlesModal.articles.length} trouvés)</h4>
                {articlesModal.articles.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Aucun article individuel enregistré pour ce type (peut-être géré en stock global consommable).</p>
                ) : (
                  <div className="table-wrap" style={{ maxHeight: '250px', overflowY: 'auto', marginTop: '0.5rem' }}>
                    <table className="table" style={{ width: '100%', fontSize: '0.85rem' }}>
                      <thead>
                        <tr>
                          <th>Réf. Article</th>
                          <th>N° de Série</th>
                          <th>Code QR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {articlesModal.articles.map((art) => (
                          <tr key={art.id}>
                            <td><strong>{art.ref_article || '—'}</strong></td>
                            <td>{art.num_serie || '—'}</td>
                            <td>{art.qr_code || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: '2rem', textAlign: 'right' }}>
              <button type="button" className="btn btn-secondary" onClick={() => { setEntreeSelectionnee(null); setArticlesModal(null); }}>
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {nouveauMode && (
        <Card titre="Nouvel arrivage de matériel">
          <form onSubmit={enregistrerEntree}>
            <Alert type="erreur">{erreur}</Alert>
            <div className="form-grille">
              <Field label="Référence de l'entrée">
                <input value={refEntree} onChange={(e) => setRefEntree(e.target.value)} required placeholder="Ex: ENT-2026-001" />
              </Field>
              <Field label="Fournisseur">
                <select value={fournisseurId} onChange={(e) => setFournisseurId(e.target.value)} required>
                  <option value="">— Sélectionner —</option>
                  {(fournisseurs || []).map((f) => (
                    <option key={f.id} value={f.id}>{f.nom_fournisseur}</option>
                  ))}
                </select>
              </Field>
              <Field label="Origine">
                <select value={origine} onChange={(e) => setOrigine(e.target.value)}>
                  {Object.entries(ORIGINES).map(([valeur, libelle]) => (
                    <option key={valeur} value={valeur}>{libelle}</option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="Document justificatif de l’entrée (obligatoire — CAME)">
              <input type="file" accept=".pdf,.jpg,.jpeg,.png" required onChange={(e) => setDocumentEntree(e.target.files?.[0] || null)} />
            </Field>
            <h3>Contenu du lot</h3>
            <LignesEditor types={types || []} lignes={lignes} onChange={setLignes} />
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Valider l'entrée en stock</button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {entrees.length === 0 ? (
          <Empty>Aucune entrée enregistrée.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Date</th>
                  <th>Origine</th>
                  <th>Fournisseur</th>
                  <th>Enregistré par</th>
                </tr>
              </thead>
              <tbody>
                {entrees.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <button
                        type="button"
                        onClick={() => ouvrirDetailEntree(e)}
                        style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', fontWeight: 'bold', padding: 0, textDecoration: 'underline' }}
                        title="Cliquer pour afficher les détails de cette entrée"
                      >
                        {e.ref_entree}
                      </button>
                    </td>
                    <td>{fmtDate(e.date_entree)}</td>
                    <td>{ORIGINES[e.origine] || e.origine}</td>
                    <td>{e.fournisseur_nom}</td>
                    <td>{e.utilisateur_nom || '—'}</td>
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
