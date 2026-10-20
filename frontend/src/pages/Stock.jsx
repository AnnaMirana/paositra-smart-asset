import { useMemo, useState } from 'react';
import { api } from '../api';
import { Badge, Card, Empty, ErreurChargement, Field, Loading, PageHeader } from '../components/ui';
import { useLoad } from '../lib/hooks';

// Pour chaque type : stock physique (en rayon au CAME), stock réservé par les bons autorisés ou validés
// pas encore sortis, et stock encore disponible pour de nouvelles autorisations.
export default function Stock() {
  const { data, loading, error, reload } = useLoad(async () => {
    const types = await api.list('types-article');
    const stocks = await Promise.all(types.map((t) => api.stock(t.id)));
    return types.map((t, i) => ({ ...t, ...stocks[i] }));
  }, []);
  const [recherche, setRecherche] = useState('');
  const [categorie, setCategorie] = useState('');

  const lignes = useMemo(() => {
    const q = recherche.trim().toLowerCase();
    return (data || []).filter(
      (t) =>
        (!categorie || t.categorie_nom === categorie) &&
        (!q || `${t.nom_type_article} ${t.marque || ''}`.toLowerCase().includes(q)),
    );
  }, [data, recherche, categorie]);

  if (loading && !data) return <Loading />;
  if (error && !data) return <ErreurChargement erreur={error} onRetry={reload} />;

  const categories = [...new Set(data.map((t) => t.categorie_nom))].sort();

  return (
    <>
      <PageHeader
        titre="Stock"
        sousTitre="Stock physique, quantités réservées par les bons en cours, et stock disponible pour de nouvelles autorisations."
      >
        <button type="button" className="btn" onClick={reload}>
          Actualiser
        </button>
      </PageHeader>

      <Card>
        <div className="filtres">
          <Field label="Rechercher">
            <input value={recherche} onChange={(e) => setRecherche(e.target.value)} placeholder="Nom ou marque…" />
          </Field>
          <Field label="Catégorie">
            <select value={categorie} onChange={(e) => setCategorie(e.target.value)}>
              <option value="">Toutes</option>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </Field>
        </div>
        {lignes.length === 0 ? (
          <Empty>Aucun type d’article à afficher.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Catégorie</th>
                  <th>Type</th>
                  <th>Marque</th>
                  <th>Suivi</th>
                  <th className="num">Stock physique</th>
                  <th className="num">Réservé</th>
                  <th className="num">Disponible à l’autorisation</th>
                </tr>
              </thead>
              <tbody>
                {lignes.map((t) => (
                  <tr key={t.id}>
                    <td>{t.categorie_nom}</td>
                    <td>
                      <strong>{t.nom_type_article}</strong>
                    </td>
                    <td>{t.marque || '—'}</td>
                    <td>{t.gestion_individuelle ? 'Individuel' : 'Par quantité'}</td>
                    <td className="num">{t.quantite_stock}</td>
                    <td className="num">{t.quantite_reservee}</td>
                    <td className="num">
                      {t.stock_disponible_pour_autorisation === 0 ? (
                        <Badge ton="rouge">0</Badge>
                      ) : (
                        <strong>{t.stock_disponible_pour_autorisation}</strong>
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