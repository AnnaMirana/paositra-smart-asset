// Liste de lignes « type d'article + quantité » (entrées et bons de sortie).
//   lignes   : [{ type_article: '3', <champQuantite>: '10' }, ...]  (valeurs en texte, comme dans un formulaire)
//   onChange : reçoit la nouvelle liste

// Fonction helper pour afficher correctement le libellé du type d'article
const libelleType = (t) => {
  if (!t) return '';
  if (typeof t === 'string') return t;
  return t.nom_type_article || t.libelle || t.nom || t.designation || JSON.stringify(t);
};

export default function LignesEditor({ types = [], lignes, onChange, champQuantite = 'quantite', libelleQuantite = 'Quantité' }) {
  const maj = (index, patch) => onChange(lignes.map((l, i) => (i === index ? { ...l, ...patch } : l)));
  const retirer = (index) => onChange(lignes.filter((_, i) => i !== index));
  const ajouter = () => onChange([...lignes, { type_article: '', [champQuantite]: '' }]);

  // Regroupe les types par catégorie dans la liste déroulante.
  const parCategorie = types.reduce((acc, t) => {
    const catNom = t.categorie_nom || t.categorie || 'Autres';
    (acc[catNom] ||= []).push(t);
    return acc;
  }, {});

  return (
    <div className="lignes-editor">
      {lignes.map((ligne, i) => {
        const type = types.find((t) => String(t.id) === String(ligne.type_article));
        return (
          <div className="ligne-form" key={i}>
            <label className="field grow">
              <span className="field-label">Type d'article</span>
              <select value={ligne.type_article} onChange={(e) => maj(i, { type_article: e.target.value })}>
                <option value="">— choisir —</option>
                {Object.entries(parCategorie).map(([categorie, liste]) => (
                  <optgroup key={categorie} label={categorie}>
                    {liste.map((t) => (
                      <option key={t.id} value={t.id}>
                        {libelleType(t)}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              {type && (
                <small>
                  {type.gestion_individuelle
                    ? 'Suivi individuel : un article par unité'
                    : 'Suivi par quantité : pas d’article individuel'}{' '}
                  · stock physique {type.quantite_stock ?? 0}
                </small>
              )}
            </label>
            <label className="field">
              <span className="field-label">{libelleQuantite}</span>
              <input
                type="number"
                min="1"
                step="1"
                value={ligne[champQuantite]}
                onChange={(e) => maj(i, { [champQuantite]: e.target.value })}
              />
            </label>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => retirer(i)}
              disabled={lignes.length === 1}
              title="Retirer cette ligne"
            >
              ✕
            </button>
          </div>
        );
      })}
      <button type="button" className="btn btn-sm" onClick={ajouter}>
        + Ajouter une ligne
      </button>
    </div>
  );
}