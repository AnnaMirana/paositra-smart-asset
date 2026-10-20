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

  const { data: entites } = useLoad(() => api.list('entites'), []);
  const { data: types } = useLoad(() => api.list('types-article'), []);
  const { data: bons, loading, error, reload } = useLoad(() => api.list('bons-sortie'), []);

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
                    <td><strong>{b.reference_bs}</strong></td>
                    <td>{fmtDate(b.date_bs)}</td>
                    <td>{b.entite_nom}</td>
                    <td>{b.utilisateur_nom}</td>
                    <td><StatutBadge statut={b.statut} /></td>
                    <td>
                      {/* Bouton Soumettre pour le demandeur */}
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

                      {/* Bouton Autoriser pour le DSID */}
                      {(b.statut === 'en_attente_autorisation' || b.statut === 'En attente d’autorisation') && peutAutoriser(user) && (
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={async () => {
                            try {
                              // Récupérer les lignes de ce bon pour les autoriser
                              const lignesBon = await api.list('lignes-bsortie', { bon_sortie: b.id });
                              if (!lignesBon || lignesBon.length === 0) {
                                alert("Aucune ligne trouvée pour ce bon.");
                                return;
                              }
                              
                              for (const ligne of lignesBon) {
                                const qteSaisie = prompt(`Quantité autorisée pour la ligne (demandée : ${ligne.quantite_demandee}) :`, ligne.quantite_demandee);
                                if (qteSaisie === null) return; // Annulé par l'utilisateur
                                
                                const quantite = parseInt(qteSaisie, 10);
                                const motif = quantite !== ligne.quantite_demandee ? prompt("Motif obligatoire (quantité modifiée) :") || "" : "";
                                
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

                      {/* Bouton Valider pour le DCA */}
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
                                
                                for (const ligne of lignesBon) {
                                  // On affiche les infos de la demande, l'autorisation et le motif du DSID s'il existe
                                  const qteAutorisee = ligne.quantite_autorisee ?? ligne.quantite_demandee;
                                  const motifDsid = ligne.motif_autorisation || ligne.motif || "Aucun motif";
                                  
                                  const messagePrompt = `Ligne — Demandé : ${ligne.quantite_demandee} | Autorisé DSID : ${qteAutorisee}\nMotif DSID : "${motifDsid}"\n\nEntrez la quantité à valider :`;
                                  
                                  const qteSaisie = prompt(messagePrompt, qteAutorisee);
                                  if (qteSaisie === null) return; // Annulé
                                  
                                  const quantite = parseInt(qteSaisie, 10);
                                  const motif = quantite !== qteAutorisee ? prompt("Motif obligatoire (quantité modifiée par rapport à l'autorisation) :") || "" : "";
                                  
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
                        {/* Bouton Effectuer la sortie pour le CAME */}
                          {(b.statut === 'valide' || b.statut === 'Validé') && peutSortir(user) && (
                            <button
                              type="button"
                              className="btn btn-sm btn-success"
                              onClick={async () => {
                                try {
                                  const dateDuJour = new Date().toISOString().slice(0, 10);
                                  const dateSortieSaisie = prompt("Entrez la date de sortie (AAAA-MM-JJ) :", dateDuJour);
                                  if (dateSortieSaisie === null) return; // Annulé

                                  await api.effectuerSortie({ 
                                    bon_sortie: b.id, 
                                    date_sortie: dateSortieSaisie 
                                  });
                                  
                                  reload();
                                  alert("Sortie physique effectuée avec succès ! Le stock a été mis à jour.");
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