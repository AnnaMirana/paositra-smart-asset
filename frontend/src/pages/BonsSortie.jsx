// src/pages/BonsSortie.jsx
import { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { Alert, Card, Empty, ErreurChargement, Field, Loading, PageHeader, StatutBadge } from '../components/ui';
import LignesEditor from '../components/LignesEditor';
import { fmtDate } from '../lib/format';
import { useLoad } from '../lib/hooks';
import { peutSoumettreRole, peutAutoriser, peutValider, peutSortir} from '../lib/roles';

export default function BonsSortie() {
  const { user } = useAuth();
  const [nouveauMode, setNouveauMode] = useState(false);
  const [reference, setReference] = useState('');
  const [entiteId, setEntiteId] = useState('');
  const [lignes, setLignes] = useState([{ type_article: '', quantite_demandee: '' }]);
  const [erreur, setErreur] = useState('');

  // États pour la modale de détail et l'affichage des articles sortis par ligne
  const [bsSelectionne, setBsSelectionne] = useState(null);
  const [articlesModal, setArticlesModal] = useState(null); // { titreType, articles: [] }
  const [loadingArticles, setLoadingArticles] = useState(false);

  const { data: entites } = useLoad(() => api.list('entites'), []);
  const { data: types } = useLoad(() => api.list('types-article'), []);
  const { data: bons, loading, error, reload } = useLoad(() => api.list('bons-sortie'), []);

  function ouvrirDetailBs(bs) {
    setBsSelectionne(bs);
    setArticlesModal(null);
  }

// Fonction pour récupérer et afficher les articles réellement sortis pour ce bon de sortie
  async function voirArticlesLigneBs(bsId, typeArticleId, nomType) {
    setLoadingArticles(true);
    try {
      // 1. Récupérer toutes les sorties enregistrées
      const toutesSorties = await api.list('sorties');
      
      // 2. Trouver la sortie correspondant à ce bon de sortie
      const sortieAssociee = (toutesSorties || []).find(s => String(s.bon_sortie) === String(bsId));
      
      let articlesFiltres = [];
      if (sortieAssociee && sortieAssociee.articles) {
        // 3. Récupérer tous les articles pour avoir leurs détails (ref, num_serie, qr_code)
        const tousArticles = await api.list('articles');
        
        // 4. Filtrer uniquement les articles présents dans cette sortie et de ce type
        articlesFiltres = (tousArticles || []).filter(a => {
          const estDansSortie = sortieAssociee.articles.includes(a.id) || sortieAssociee.articles.includes(String(a.id));
          const estDuBonType = String(a.type_article) === String(typeArticleId);
          return estDansSortie && estDuBonType;
        });
      } else {
        // Fallback si la sortie n'a pas encore de liste d'articles directs, on liste par type du bon
        const tousArticles = await api.list('articles');
        articlesFiltres = (tousArticles || []).filter(a => String(a.type_article) === String(typeArticleId));
      }
      
      setArticlesModal({
        titre: nomType,
        articles: articlesFiltres
      });
    } catch (err) {
      alert("Erreur lors du chargement des articles sortis : " + err.message);
    } finally {
      setLoadingArticles(false);
    }
  }

  async function creerBon(e) {
    e.preventDefault();
    setErreur('');
    try {
      const bs = await api.create('bons-sortie', {
        reference_bs: reference.trim(),
        date_bs: new Date().toISOString().slice(0, 10),
        entite: entiteId,
      });
      for (const l of lignes) {
        if (l.type_article && l.quantite_demandee) {
          await api.ajouterLigneBon(bs.id, {
            type_article: l.type_article,
            quantite_demandee: parseInt(l.quantite_demandee, 10),
          });
        }
      }
      setNouveauMode(false);
      setReference('');
      setLignes([{ type_article: '', quantite_demandee: '' }]);
      reload();
    } catch (err) {
      setErreur(err.message);
    }
  }

  if (loading && !bons) return <Loading />;
  if (error && !bons) return <ErreurChargement erreur={error} onRetry={reload} />;

  return (
    <>
      <PageHeader titre="Bons de Sortie" sousTitre="Gestion et suivi du workflow de demande de matériels.">
        {peutSoumettreRole(user) && (
          <button type="button" className="btn btn-primary" onClick={() => setNouveauMode(!nouveauMode)}>
            {nouveauMode ? 'Fermer' : '+ Nouveau bon de sortie'}
          </button>
        )}
      </PageHeader>

      {/* MODALE DE DÉTAIL DU BON DE SORTIE */}
      {bsSelectionne && (
        <div className="modal-backdrop" style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="card" style={{ background: '#fff', padding: '2rem', borderRadius: '8px', width: '90%', maxWidth: '850px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2>Détail du Bon de Sortie : {bsSelectionne.reference_bs}</h2>
            <hr style={{ margin: '1rem 0' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <p><strong>Date :</strong> {fmtDate(bsSelectionne.date_bs)}</p>
              <p><strong>Entité bénéficiaire :</strong> {bsSelectionne.entite_nom || '—'}</p>
              <p><strong>Demandeur :</strong> {bsSelectionne.utilisateur_nom || '—'}</p>
              <p><strong>Statut actuel :</strong> <StatutBadge statut={bsSelectionne.statut} /></p>
            </div>

            <h3 style={{ marginTop: '1.5rem' }}>Lignes et suivi du workflow (Cliquez sur un chiffre validé)</h3>
            {(!bsSelectionne.lignes || bsSelectionne.lignes.length === 0) ? (
              <p>Aucune ligne enregistrée pour ce bon.</p>
            ) : (
              <table className="table" style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.9rem' }}>
                <thead>
                  <tr>
                    <th>Type d'article</th>
                    <th>Demandé</th>
                    <th>Autorisé (DSID)</th>
                    <th>Validé (DCA)</th>
                    <th>État</th>
                  </tr>
                </thead>
                <tbody>
                  {bsSelectionne.lignes.map((l, index) => {
                    const motifDsid = l.motif_autorisation || '—';
                    const motifDca = l.motif_validation || '—';
                    const qteValidee = l.quantite_validee ?? 0;

                    return (
                      <tr key={index}>
                        <td>
                          <strong>{l.type_article_nom || 'Article'}</strong>
                          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                            {motifDsid !== '—' && <span>DSID: {motifDsid}<br/></span>}
                            {motifDca !== '—' && <span>DCA: {motifDca}</span>}
                          </div>
                        </td>
                        <td>{l.quantite_demandee}</td>
                        <td>{l.quantite_autorisee ?? '—'}</td>
                        <td>
                          {qteValidee > 0 ? (
                            <button
                              type="button"
                              onClick={() => voirArticlesLigneBs(bsSelectionne.id, l.type_article, l.type_article_nom)}
                              style={{ background: '#e0f2fe', border: '1px solid #bae6fd', color: '#0369a1', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                              title="Cliquer pour afficher les articles"
                            >
                              {qteValidee} unité(s) 🔍
                            </button>
                          ) : (
                            <span>—</span>
                          )}
                        </td>
                        <td><span className="badge">{l.etat_ligne}</span></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

            {/* SOUS-SECTION : ARTICLES SORTIS / ASSOCIÉS */}
            {loadingArticles && <p style={{ marginTop: '1rem' }}>Chargement des articles...</p>}
            
            {articlesModal && (
              <div style={{ marginTop: '2rem', background: '#f8fafc', padding: '1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <h4>Articles concernés pour : {articlesModal.titre}</h4>
                {articlesModal.articles.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Aucun article individuel trouvé.</p>
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
              <button type="button" className="btn btn-secondary" onClick={() => { setBsSelectionne(null); setArticlesModal(null); }}>
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {nouveauMode && (
        <Card titre="Créer un nouveau Bon de Sortie">
          <form onSubmit={creerBon}>
            <Alert type="erreur">{erreur}</Alert>
            <div className="form-grille">
              <Field label="Référence du Bon">
                <input value={reference} onChange={(e) => setReference(e.target.value)} required placeholder="Ex: BS-2026-001" />
              </Field>
              <Field label="Entité bénéficiaire">
                <select value={entiteId} onChange={(e) => setEntiteId(e.target.value)} required>
                  <option value="">— Sélectionner —</option>
                  {(entites || []).map((e) => (
                    <option key={e.id} value={e.id}>{e.nom_entite}</option>
                  ))}
                </select>
              </Field>
            </div>
            <h3>Articles demandés</h3>
            <LignesEditor
              types={types || []}
              lignes={lignes}
              onChange={setLignes}
              champQuantite="quantite_demandee"
              libelleQuantite="Qté demandée"
            />
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Enregistrer en brouillon</button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {bons.length === 0 ? (
          <Empty>Aucun bon de sortie enregistré.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Date</th>
                  <th>Entité</th>
                  <th>Demandeur</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {bons.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <button
                        type="button"
                        onClick={() => ouvrirDetailBs(b)}
                        style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', fontWeight: 'bold', padding: 0, textDecoration: 'underline' }}
                        title="Cliquer pour afficher les détails de ce bon"
                      >
                        {b.reference_bs}
                      </button>
                    </td>
                    <td>{fmtDate(b.date_bs)}</td>
                    <td>{b.entite_nom}</td>
                    <td>{b.utilisateur_nom}</td>
                    <td><StatutBadge statut={b.statut} /></td>
                    <td>
                      {(b.statut === 'brouillon' || b.statut === 'Brouillon') && peutSoumettreRole(user) && (
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={async () => {
                            try {
                              await api.soumettre(b.id);
                              reload();
                            } catch (err) {
                              alert("Erreur lors de la soumission : " + err.message);
                            }
                          }}
                        >
                          Soumettre
                        </button>
                      )}

                      {(b.statut === 'en_attente_autorisation' || b.statut === 'En attente d’autorisation') && peutAutoriser(user) && (
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={async () => {
                            try {
                              const lignesBon = await api.list('lignes-bsortie', { bon_sortie: b.id });
                              if (!lignesBon || lignesBon.length === 0) {
                                alert("Aucune ligne trouvée pour ce bon.");
                                return;
                              }
                              for (const ligne of lignesBon) {
                                const nomArticle = ligne.type_article_nom || "Article";
                                const qteSaisie = prompt(`Quantité autorisée pour la ligne (${nomArticle} demandée : ${ligne.quantite_demandee}) :`, ligne.quantite_demandee);
                                if (qteSaisie === null) return;
                                const quantite = parseInt(qteSaisie, 10);
                                const motif = quantite !== ligne.quantite_demandee ? prompt(`Motif obligatoire pour ${nomArticle} :`) || "" : "";
                                await api.autoriser(ligne.id, quantite, motif);
                              }
                              reload();
                              alert("Bon de sortie autorisé avec succès !");
                            } catch (err) {
                              alert("Erreur lors de l'autorisation : " + err.message);
                            }
                          }}
                        >
                          Autoriser (DSID)
                        </button>
                      )}

                      {(b.statut === 'en_attente_validation' || b.statut === 'En attente de validation') && peutValider(user) && (
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={async () => {
                            try {
                              const lignesBon = await api.list('lignes-bsortie', { bon_sortie: b.id });
                              if (!lignesBon || lignesBon.length === 0) {
                                alert("Aucune ligne trouvée pour ce bon.");
                                return;
                              }
                              const lignesAValider = lignesBon.filter(l => l.etat_ligne === 'autorisee' || (l.quantite_autorisee !== null && l.quantite_autorisee > 0));
                              if (lignesAValider.length === 0) {
                                alert("Toutes les lignes ont été refusées par le DSID.");
                                return;
                              }
                              for (const ligne of lignesAValider) {
                                const nomArticle = ligne.type_article_nom || "Article";
                                const qteAutorisee = ligne.quantite_autorisee ?? ligne.quantite_demandee;
                                const motifDsid = ligne.motif_autorisation || "Aucun motif";
                                const messagePrompt = `Article : ${nomArticle}\nDemandé : ${ligne.quantite_demandee} | Autorisé DSID : ${qteAutorisee}\nMotif : "${motifDsid}"\n\nEntrez la quantité à valider :`;
                                const qteSaisie = prompt(messagePrompt, qteAutorisee);
                                if (qteSaisie === null) return;
                                const quantite = parseInt(qteSaisie, 10);
                                const motif = quantite !== qteAutorisee ? prompt(`Motif obligatoire pour ${nomArticle} :`) || "" : "";
                                await api.valider(ligne.id, quantite, motif);
                              }
                              reload();
                              alert("Bon de sortie validé avec succès par le DCA !");
                            } catch (err) {
                              alert("Erreur lors de la validation : " + err.message);
                            }
                          }}
                        >
                          Valider (DCA)
                        </button>
                      )}

                      {(b.statut === 'valide' || b.statut === 'Validé') && peutSortir(user) && (
                        <button
                          type="button"
                          className="btn btn-sm btn-success"
                          onClick={async () => {
                            try {
                              const dateDuJour = new Date().toISOString().slice(0, 10);
                              const dateSortieSaisie = prompt("Entrez la date de sortie (AAAA-MM-JJ) :", dateDuJour);
                              if (dateSortieSaisie === null) return;
                              await api.effectuerSortie({ bon_sortie: b.id, date_sortie: dateSortieSaisie });
                              reload();
                              alert("Sortie physique effectuée avec succès !");
                            } catch (err) {
                              alert("Erreur lors de la sortie physique : " + err.message);
                            }
                          }}
                        >
                          Effectuer Sortie (CAME)
                        </button>
                      )}
                    </td>
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
