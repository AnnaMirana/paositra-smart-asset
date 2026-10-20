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
  const [lignes, setLignes] = useState([{ type_article: '', quantite: '' }]);
  const [erreur, setErreur] = useState('');

  const { data: fournisseurs } = useLoad(() => api.list('fournisseurs'), []);
  const { data: types } = useLoad(() => api.list('types-article'), []);
  const { data: entrees, loading, error, reload } = useLoad(() => api.list('entrees'), []);

  async function enregistrerEntree(e) {
    e.preventDefault();
    setErreur('');
    try {
      const entree = await api.create('entrees', {
        ref_entree: refEntree.trim(),
        date_entree: new Date().toISOString().slice(0, 10),
        origine,
        fournisseur: fournisseurId,
      });
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
      setLignes([{ type_article: '', quantite: '' }]);
      reload();
    } catch (err) {
      setErreur(err.message);
    }
  }

  if (loading && !entrees) return <Loading />;
  if (error && !entrees) return <ErreurChargement erreur={error} onRetry={reload} />;

  return (
    <>
      <PageHeader titre="Entrées en Stock" sousTitre="Enregistrement des approvisionnements et dons.">
        {peutEcrire(user) && (
          <button type="button" className="btn btn-primary" onClick={() => setNouveauMode(!nouveauMode)}>
            {nouveauMode ? 'Fermer' : '+ Nouvelle entrée'}
          </button>
        )}
      </PageHeader>

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
                    <td><strong>{e.ref_entree}</strong></td>
                    <td>{fmtDate(e.date_entree)}</td>
                    <td>{ORIGINES[e.origine] || e.origine}</td>
                    <td>{e.fournisseur_nom}</td>
                    <td>{e.utilisateur_nom}</td>
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