import { useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import {
  Alert,
  Card,
  Empty,
  ErreurChargement,
  Field,
  Loading,
  PageHeader,
} from '../components/ui';

const ONGLET = [
  'entites',
  'categories',
  'types',
  'fournisseurs',
];

const LIBELLES = {
  entites: 'Entités',
  categories: 'Catégories',
  types: 'Types d’articles',
  fournisseurs: 'Fournisseurs',
};

const RESSOURCES = {
  entites: 'entites',
  categories: 'categories',
  types: 'types-article',
  fournisseurs: 'fournisseurs',
};

const FORMULAIRES = {
  entites: {
    nom_entite: '',
    sigle_entite: '',
    type_entite: 'direction',
  },
  categories: {
    nom_categorie: '',
  },
  types: {
    nom_type_article: '',
    categorie: '',
    marque: '',
    caracteristique: '',
    gestion_individuelle: false,
  },
  fournisseurs: {
    nom_fournisseur: '',
    informations: '',
  },
};

export default function Referentiels() {
  const { user } = useAuth();

  const [onglet, setOnglet] = useState('entites');

  const [donnees, setDonnees] = useState({
    entites: [],
    categories: [],
    types: [],
    fournisseurs: [],
  });

  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState('');
  const [message, setMessage] = useState('');

  const [form, setForm] = useState({ ...FORMULAIRES.entites });
  const [elementModifie, setElementModifie] = useState(null);

  const estAdmin = Boolean(
    user && (user.role === 'admin' || user.is_superuser)
  );

  async function charger() {
    setLoading(true);
    setErreur('');

    try {
      const [entites, categories, types, fournisseurs] =
        await Promise.all([
          api.list('entites'),
          api.list('categories'),
          api.list('types-article'),
          api.list('fournisseurs'),
        ]);

      setDonnees({
        entites,
        categories,
        types,
        fournisseurs,
      });
    } catch (e) {
      setErreur(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    charger();
  }, []);

  function changer(cle, valeur) {
    setForm((ancien) => ({
      ...ancien,
      [cle]: valeur,
    }));
  }

  function changerOnglet(nouvelOnglet) {
    setOnglet(nouvelOnglet);
    setForm({ ...FORMULAIRES[nouvelOnglet] });
    setElementModifie(null);
    setErreur('');
    setMessage('');
  }

  function preparerModification(element) {
    setElementModifie(element.id);

    if (onglet === 'entites') {
      setForm({
        nom_entite: element.nom_entite || '',
        sigle_entite: element.sigle_entite || '',
        type_entite: element.type_entite || 'direction',
      });
    }

    if (onglet === 'categories') {
      setForm({
        nom_categorie: element.nom_categorie || '',
      });
    }

    if (onglet === 'types') {
      setForm({
        nom_type_article: element.nom_type_article || '',
        categorie: element.categorie || '',
        marque: element.marque || '',
        caracteristique: element.caracteristique || '',
        gestion_individuelle: Boolean(element.gestion_individuelle),
      });
    }

    if (onglet === 'fournisseurs') {
      setForm({
        nom_fournisseur: element.nom_fournisseur || '',
        informations: element.informations || '',
      });
    }

    setErreur('');
    setMessage('');
  }

  function annulerModification() {
    setElementModifie(null);
    setForm({ ...FORMULAIRES[onglet] });
    setErreur('');
    setMessage('');
  }

  function construireDonnees() {
    if (onglet === 'entites') {
      return {
        nom_entite: form.nom_entite.trim(),
        sigle_entite: form.sigle_entite.trim(),
        type_entite: form.type_entite,
      };
    }

    if (onglet === 'categories') {
      return {
        nom_categorie: form.nom_categorie.trim(),
      };
    }

    if (onglet === 'types') {
      return {
        nom_type_article: form.nom_type_article.trim(),
        categorie: Number(form.categorie),
        marque: form.marque.trim(),
        caracteristique: form.caracteristique.trim(),
        gestion_individuelle: Boolean(form.gestion_individuelle),
      };
    }

    return {
      nom_fournisseur: form.nom_fournisseur.trim(),
      informations: form.informations.trim(),
    };
  }

  async function enregistrer(e) {
    e.preventDefault();

    setErreur('');
    setMessage('');

    try {
      const ressource = RESSOURCES[onglet];
      const donneesFormulaire = construireDonnees();

      if (elementModifie !== null) {
        await api.update(
          ressource,
          elementModifie,
          donneesFormulaire
        );

        setMessage('Modification enregistrée.');
      } else {
        await api.create(
          ressource,
          donneesFormulaire
        );

        setMessage('Enregistrement effectué.');
      }

      setElementModifie(null);
      setForm({ ...FORMULAIRES[onglet] });

      await charger();
    } catch (err) {
      setErreur(err.message);
    }
  }

  function exporter(format) {
    api.exporter(RESSOURCES[onglet], format);
  }

  if (loading) {
    return <Loading />;
  }

  if (
    erreur &&
    !Object.values(donnees).some((liste) => liste.length > 0)
  ) {
    return (
      <ErreurChargement
        erreur={erreur}
        onRetry={charger}
      />
    );
  }

  return (
    <>
      <PageHeader
        titre="Référentiels"
        sousTitre="Gestion des entités, catégories, types d’articles et fournisseurs."
      >
        <button
          type="button"
          className="btn"
          onClick={() => exporter('excel')}
        >
          Excel
        </button>

        <button
          type="button"
          className="btn"
          onClick={() => exporter('pdf')}
        >
          PDF
        </button>
      </PageHeader>

      <div className="onglets">
        {ONGLET.map((nom) => (
          <button
            key={nom}
            type="button"
            className={`onglet ${onglet === nom ? 'actif' : ''}`}
            onClick={() => changerOnglet(nom)}
          >
            {LIBELLES[nom]}
          </button>
        ))}
      </div>

      {erreur && (
        <Alert type="erreur">
          {erreur}
        </Alert>
      )}

      {message && (
        <Alert type="ok">
          {message}
        </Alert>
      )}

      {estAdmin && (
        <Card
          titre={
            elementModifie !== null
              ? `Modifier : ${LIBELLES[onglet]}`
              : `Ajouter : ${LIBELLES[onglet]}`
          }
        >
          <form onSubmit={enregistrer}>
            {onglet === 'entites' && (
              <div className="form-grille">
                <Field label="Nom de l’entité">
                  <input
                    required
                    value={form.nom_entite}
                    onChange={(e) =>
                      changer('nom_entite', e.target.value)
                    }
                  />
                </Field>

                <Field label="Sigle (facultatif)">
                  <input
                    value={form.sigle_entite}
                    onChange={(e) =>
                      changer('sigle_entite', e.target.value)
                    }
                  />
                </Field>

                <Field label="Type d’entité">
                  <select
                    value={form.type_entite}
                    onChange={(e) =>
                      changer('type_entite', e.target.value)
                    }
                  >
                    <option value="direction">Direction</option>
                    <option value="agence">Agence</option>
                    <option value="depot">Dépôt</option>
                  </select>
                </Field>
              </div>
            )}

            {onglet === 'categories' && (
              <Field label="Nom de la catégorie">
                <input
                  required
                  value={form.nom_categorie}
                  onChange={(e) =>
                    changer('nom_categorie', e.target.value)
                  }
                />
              </Field>
            )}

            {onglet === 'types' && (
              <div className="form-grille">
                <Field label="Nom du type d’article">
                  <input
                    required
                    value={form.nom_type_article}
                    onChange={(e) =>
                      changer('nom_type_article', e.target.value)
                    }
                  />
                </Field>

                <Field label="Catégorie">
                  <select
                    required
                    value={form.categorie}
                    onChange={(e) =>
                      changer('categorie', e.target.value)
                    }
                  >
                    <option value="">— Choisir une catégorie —</option>

                    {donnees.categories.map((categorie) => (
                      <option
                        key={categorie.id}
                        value={categorie.id}
                      >
                        {categorie.nom_categorie}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Marque">
                  <input
                    value={form.marque}
                    onChange={(e) =>
                      changer('marque', e.target.value)
                    }
                  />
                </Field>

                <Field label="Caractéristiques">
                  <textarea
                    value={form.caracteristique}
                    onChange={(e) =>
                      changer('caracteristique', e.target.value)
                    }
                  />
                </Field>

                <label>
                  <input
                    type="checkbox"
                    checked={form.gestion_individuelle}
                    onChange={(e) =>
                      changer(
                        'gestion_individuelle',
                        e.target.checked
                      )
                    }
                  />
                  Gestion individuelle (un article par exemplaire)
                </label>
              </div>
            )}

            {onglet === 'fournisseurs' && (
              <div className="form-grille">
                <Field label="Nom du fournisseur">
                  <input
                    required
                    value={form.nom_fournisseur}
                    onChange={(e) =>
                      changer('nom_fournisseur', e.target.value)
                    }
                  />
                </Field>

                <Field label="Informations">
                  <textarea
                    value={form.informations}
                    onChange={(e) =>
                      changer('informations', e.target.value)
                    }
                  />
                </Field>
              </div>
            )}

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary"
              >
                {elementModifie !== null
                  ? 'Enregistrer les modifications'
                  : 'Ajouter'}
              </button>

              {elementModifie !== null && (
                <button
                  type="button"
                  className="btn"
                  onClick={annulerModification}
                >
                  Annuler
                </button>
              )}
            </div>
          </form>
        </Card>
      )}

      <Card titre={`Liste des ${LIBELLES[onglet].toLowerCase()}`}>
        {onglet === 'entites' && (
          donnees.entites.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Nom</th>
                    <th>Sigle</th>
                    <th>Type</th>
                    {estAdmin && <th>Actions</th>}
                  </tr>
                </thead>

                <tbody>
                  {donnees.entites.map((entite) => (
                    <tr key={entite.id}>
                      <td>{entite.nom_entite}</td>
                      <td>{entite.sigle_entite || '—'}</td>
                      <td>{entite.type_entite}</td>

                      {estAdmin && (
                        <td>
                          <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() =>
                              preparerModification(entite)
                            }
                          >
                            Modifier
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Aucune entité.</Empty>
          )
        )}

        {onglet === 'categories' && (
          donnees.categories.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Catégorie</th>
                    {estAdmin && <th>Actions</th>}
                  </tr>
                </thead>

                <tbody>
                  {donnees.categories.map((categorie) => (
                    <tr key={categorie.id}>
                      <td>{categorie.nom_categorie}</td>

                      {estAdmin && (
                        <td>
                          <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() =>
                              preparerModification(categorie)
                            }
                          >
                            Modifier
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Aucune catégorie.</Empty>
          )
        )}

        {onglet === 'types' && (
          donnees.types.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Catégorie</th>
                    <th>Marque</th>
                    <th>Stock</th>
                    <th>Gestion</th>
                    {estAdmin && <th>Actions</th>}
                  </tr>
                </thead>

                <tbody>
                  {donnees.types.map((type) => (
                    <tr key={type.id}>
                      <td>{type.nom_type_article}</td>
                      <td>{type.categorie_nom}</td>
                      <td>{type.marque || '—'}</td>
                      <td>{type.quantite_stock}</td>
                      <td>
                        {type.gestion_individuelle
                          ? 'Individuelle'
                          : 'Quantité'}
                      </td>

                      {estAdmin && (
                        <td>
                          <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() =>
                              preparerModification(type)
                            }
                          >
                            Modifier
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Aucun type d’article.</Empty>
          )
        )}

        {onglet === 'fournisseurs' && (
          donnees.fournisseurs.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Fournisseur</th>
                    <th>Informations</th>
                    {estAdmin && <th>Actions</th>}
                  </tr>
                </thead>

                <tbody>
                  {donnees.fournisseurs.map((fournisseur) => (
                    <tr key={fournisseur.id}>
                      <td>{fournisseur.nom_fournisseur}</td>
                      <td>{fournisseur.informations || '—'}</td>

                      {estAdmin && (
                        <td>
                          <button
                            type="button"
                            className="btn btn-sm"
                            onClick={() =>
                              preparerModification(fournisseur)
                            }
                          >
                            Modifier
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>Aucun fournisseur.</Empty>
          )
        )}
      </Card>
    </>
  );
}