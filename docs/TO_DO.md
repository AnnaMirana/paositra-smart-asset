# TODO — PAOSITRA SMART ASSET

## Ce qui est déjà fait

 Comprendre globalement le fonctionnement du projet.
 Poser les questions importantes à l'encadreur.
 Clarifier le fonctionnement des entrées et des sorties.
 Comprendre le circuit du Bon de Sortie et de sa validation.
 Clarifier les principaux rôles.
 Clarifier le principe du QR par article.
 Commencer à définir les règles métier.
 Commencer le MCD.

## Maintenant

### Conception

 Finir le MCD simple.
 Vérifier que chaque entité est vraiment utile.
 Vérifier les relations et les cardinalités.
 [ ] Noter les points encore à confirmer avec l'encadreur.
 [ ] Faire valider le modèle avant de commencer à coder.

### Base de données

 [ ] Créer PostgreSQL.
 [ ] Créer les tables à partir du MCD.
 [ ] Ajouter les relations importantes.
 [ ] Préparer quelques fausses données pour les tests.

### Backend

 [ ] Mettre en place Django + Django REST Framework.
 [ ] Créer les modèles.
 [ ] Faire les migrations.
 [ ] Créer les premières API.
 [ ] Tester les API.

### Fonctions principales

 [ ] Connexion utilisateur.
 [ ] Gestion des catégories et types.
 [ ] Gestion des articles.
 [ ] Enregistrer les entrées.
 [ ] Gérer les Bons de Sortie.
 [ ] Gérer la validation.
 [ ] Gérer les quantités demandées / autorisées / livrées.
 [ ] Mettre à jour le stock.
 [ ] Enregistrer les mouvements.
 [ ] Afficher l'historique d'un article.

### Cas importants

 [ ] Gérer les retours.
 [ ] Gérer les écarts d'inventaire.
 [ ] Ajouter une alerte en cas d'écart.
 [ ] Gérer les corrections sans supprimer l'ancienne information.
 [ ] Garder la trace de l'utilisateur qui effectue les opérations.

### Frontend

 [ ] Mettre en place React.
 [ ] Faire une connexion simple.
 [ ] Faire les pages principales.
 [ ] Afficher les articles et le stock.
 [ ] Afficher les entrées et sorties.
 [ ] Afficher les validations.
 [ ] Afficher l'historique.

### QR

 [ ] Générer un QR pour identifier un article.
 [ ] Scanner le QR.
 [ ] Retrouver l'article.
 [ ] Afficher ses informations et son historique.

### Fin du projet

 [ ] Faire les tests.
 [ ] Corriger les bugs.
 [ ] Vérifier les droits d'accès.
 [ ] Ajouter seulement les améliorations utiles si le temps le permet.
 [ ] Faire la documentation.
 [ ] Préparer la démonstration.
 [ ] Préparer les explications pour la soutenance.

## À garder en tête

 Le projet doit rester faisable en 3 mois.
 Faire d'abord le nécessaire avant les fonctionnalités secondaires.
 Ne pas ajouter une table juste pour rendre le projet plus compliqué.
 Les règles métier encore floues doivent être confirmées avec l'encadreur.
 Les données de test sont fictives.
 PostgreSQL dès le début.
 Le but est d'avoir une plateforme simple, fonctionnelle, propre et défendable.
 Si une fonctionnalité devient trop compliquée sans être indispensable, chercher d'abord une version plus simple.


Les trois mois restants : maintenant on doit produire

Et là je suis entièrement d'accord avec ton inquiétude.

Tu as déjà fait :

Compréhension
      ↓
Questions métier
      ↓
Cadrage
      ↓
Règles métier
      ↓
MCD

Maintenant il faut passer à :

MCD
 ↓
PostgreSQL
 ↓
Django
 ↓
API
 ↓
React
 ↓
QR
 ↓
Tests
 ↓
Documentation
 ↓
Démonstration

Donc je répartirais le reste comme ça :

Phase 1 — Base technique

PostgreSQL + Django + structure du projet.

Phase 2 — Backend

Les modèles :

Catégorie
Type article
Article
Fournisseur
Entrée
Ligne entrée
Direction
Bon sortie
Ligne sortie
Sortie
Mouvement
Utilisateur

Puis les API.

Phase 3 — Frontend

Commencer avec :

Connexion
Dashboard
Stock
Entrées
Bons de sortie
Sorties
Articles
Historique
Phase 4 — QR

Un article :

REF001
QR001

Scan → fiche article → historique.

Phase 5 — Tests + corrections

Tester le vrai scénario complet :

Entrée de 20 laptops
        ↓
20 articles physiques
        ↓
Stock +20
        ↓
Direction demande 10
        ↓
Validation
        ↓
Sortie de 10 articles précis
        ↓
Stock -10
        ↓
Historique de chaque article
Phase 6 — Finalisation

Documentation + sécurité + tests + démonstration + soutenance.
C'est une excellente décision ! Mettre en place ce **filtre par année** dans la modale d'historique des articles individuels (`Articles.jsx`) est une solution élégante, professionnelle et parfaite pour le jury : elle conserve 100% de la traçabilité légale exigée tout en gardant une interface propre et fluide.

Voici comment modifier ton fichier **`Articles.jsx`** pour intégrer ce sélecteur/filtre par année dans la modale d'historique des articles :

```jsx
// src/pages/Articles.jsx
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

```

### 🚀 Prochaine étape :

Enregistre ce fichier `Articles.jsx`. Tu peux maintenant faire un commit Git pour sceller cette magnifique fonctionnalité de filtrage par année :

```bash
git add .
git commit -m "feat: ajout du filtre par année dans la modale d'historique des articles individuels"

```

Veux-tu que l'on prévoie également l'interface ou le bouton pour la réinitialisation des consommables selon ta convenance ?