// src/pages/Referentiels.jsx
import { useState } from 'react';
import { api } from '../api';
import { Card, Empty, ErreurChargement, Loading, PageHeader } from '../components/ui';
import { useLoad } from '../lib/hooks';

export default function Referentiels() {
  const [onglet, setOnglet] = useState('entites');

  const { data: entites, loading: l1, error: e1 } = useLoad(() => api.list('entites'), []);
  const { data: categories, loading: l2, error: e2 } = useLoad(() => api.list('categories'), []);
  const { data: fournisseurs, loading: l3, error: e3 } = useLoad(() => api.list('fournisseurs'), []);

  if ((l1 || l2 || l3) && !entites) return <Loading />;
  if (e1 || e2 || e3) return <ErreurChargement erreur={e1 || e2 || e3} />;

  return (
    <>
      <PageHeader titre="Référentiels" sousTitre="Gestion des structures, catégories et partenaires." />

      <div className="onglets">
        <button type="button" className={`onglet ${onglet === 'entites' ? 'actif' : ''}`} onClick={() => setOnglet('entites')}>
          Entités ({entites?.length || 0})
        </button>
        <button type="button" className={`onglet ${onglet === 'categories' ? 'actif' : ''}`} onClick={() => setOnglet('categories')}>
          Catégories ({categories?.length || 0})
        </button>
        <button type="button" className={`onglet ${onglet === 'fournisseurs' ? 'actif' : ''}`} onClick={() => setOnglet('fournisseurs')}>
          Fournisseurs ({fournisseurs?.length || 0})
        </button>
      </div>

      <Card>
        {onglet === 'entites' && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Nom</th><th>Sigle</th><th>Type</th></tr>
              </thead>
              <tbody>
                {(entites || []).map((e) => (
                  <tr key={e.id}><td><strong>{e.nom_entite}</strong></td><td>{e.sigle_entite || '—'}</td><td>{e.type_entite}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {onglet === 'categories' && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Nom de la catégorie</th></tr>
              </thead>
              <tbody>
                {(categories || []).map((c) => (
                  <tr key={c.id}><td><strong>{c.nom_categorie}</strong></td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {onglet === 'fournisseurs' && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Nom du fournisseur</th><th>Informations</th></tr>
              </thead>
              <tbody>
                {(fournisseurs || []).map((f) => (
                  <tr key={f.id}><td><strong>{f.nom_fournisseur}</strong></td><td>{f.informations || '—'}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}