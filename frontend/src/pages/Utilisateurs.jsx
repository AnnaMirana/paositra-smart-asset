import { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Alert,
  Card,
  Empty,
  ErreurChargement,
  Field,
  Loading,
  PageHeader,
} from '../components/ui';

const ROLES = [
  { value: 'admin', label: 'Administrateur' },
  { value: 'agent_dsid', label: 'Agent DSID' },
  { value: 'agent_validation', label: 'Agent de validation (DCA)' },
  { value: 'agent_came', label: 'Agent CAME' },
  { value: 'demandeur', label: 'Demandeur' },
  { value: 'agent_direction', label: 'Agent de direction' },
  { value: 'auditeur', label: 'Auditeur' },
];

const FORM_INITIAL = {
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  role: 'demandeur',
  entite: '',
  actif: true,
};

export default function Utilisateurs() {
  const [utilisateurs, setUtilisateurs] = useState([]);
  const [entites, setEntites] = useState([]);
  const [form, setForm] = useState(FORM_INITIAL);

  const [loading, setLoading] = useState(true);
  const [enregistrement, setEnregistrement] = useState(false);
  const [erreur, setErreur] = useState('');
  const [message, setMessage] = useState('');

  async function charger() {
    setLoading(true);
    setErreur('');

    try {
      const [comptes, listeEntites] = await Promise.all([
        api.list('utilisateurs'),
        api.list('entites'),
      ]);

      setUtilisateurs(comptes);
      setEntites(listeEntites);
    } catch (e) {
      setErreur(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    charger();
  }, []);

  function changer(champ, valeur) {
    setForm((ancien) => ({
      ...ancien,
      [champ]: valeur,
    }));
  }

  async function creerUtilisateur(e) {
    e.preventDefault();

    setErreur('');
    setMessage('');

    if (form.role === 'demandeur' && !form.entite) {
      setErreur('Sélectionnez une entité pour ce compte Demandeur.');
      return;
    }

    setEnregistrement(true);

    try {
      const donnees = {
        username: form.username.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        role: form.role,
        actif: form.actif,
        entites: form.role === 'demandeur'
          ? [Number(form.entite)]
          : [],
      };

      await api.create('utilisateurs', donnees);

      setForm(FORM_INITIAL);
      setMessage('Compte créé avec succès.');

      await charger();
    } catch (e) {
      setErreur(e.message);
    } finally {
      setEnregistrement(false);
    }
  }

  async function changerStatut(utilisateur) {
    setErreur('');
    setMessage('');

    try {
      await api.update('utilisateurs', utilisateur.id, {
        actif: !utilisateur.actif,
      });

      setMessage(
        `Le compte ${utilisateur.username} a été ${
          utilisateur.actif ? 'désactivé' : 'activé'
        }.`
      );

      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  function nomRole(role) {
    const trouve = ROLES.find((r) => r.value === role);
    return trouve ? trouve.label : role;
  }

  function nomEntite(utilisateur) {
    if (!utilisateur.entites || utilisateur.entites.length === 0) {
      return '—';
    }

    const entite = entites.find(
      (e) => e.id === utilisateur.entites[0]
    );

    return entite ? entite.nom_entite : 'Entité inconnue';
  }

  if (loading) {
    return <Loading />;
  }

  if (erreur && utilisateurs.length === 0) {
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
        titre="Gestion des utilisateurs"
        sousTitre="Création et gestion des comptes de la plateforme."
      />

      {erreur && <Alert type="erreur">{erreur}</Alert>}
      {message && <Alert type="ok">{message}</Alert>}

      <Card titre="Créer un compte utilisateur">
        <form onSubmit={creerUtilisateur}>
          <div className="form-grille">
            <Field label="Nom d'utilisateur">
              <input
                type="text"
                value={form.username}
                onChange={(e) => changer('username', e.target.value)}
                required
                autoComplete="off"
              />
            </Field>

            <Field label="Mot de passe">
              <input
                type="password"
                value={form.password}
                onChange={(e) => changer('password', e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </Field>

            <Field label="Prénom">
              <input
                type="text"
                value={form.first_name}
                onChange={(e) => changer('first_name', e.target.value)}
              />
            </Field>

            <Field label="Nom">
              <input
                type="text"
                value={form.last_name}
                onChange={(e) => changer('last_name', e.target.value)}
              />
            </Field>

            <Field label="Rôle">
              <select
                value={form.role}
                onChange={(e) => {
                  changer('role', e.target.value);
                  changer('entite', '');
                }}
              >
                {ROLES.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </Field>

            {form.role === 'demandeur' && (
              <Field label="Entité associée">
                <select
                  value={form.entite}
                  onChange={(e) => changer('entite', e.target.value)}
                  required
                >
                  <option value="">— Sélectionner une entité —</option>

                  {entites.map((entite) => (
                    <option key={entite.id} value={entite.id}>
                      {entite.nom_entite}
                    </option>
                  ))}
                </select>
              </Field>
            )}
          </div>

          {form.role === 'demandeur' && (
            <Alert type="info">
              Ce compte sera partagé par les agents autorisés de cette
              entité. Une entité ne peut posséder qu'un seul compte
              Demandeur.
            </Alert>
          )}

          <label className="form-checkbox">
            <input
              type="checkbox"
              checked={form.actif}
              onChange={(e) => changer('actif', e.target.checked)}
            />
            Compte actif
          </label>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={enregistrement}
            >
              {enregistrement ? 'Création...' : 'Créer le compte'}
            </button>
          </div>
        </form>
      </Card>

      <Card titre="Comptes existants">
        {utilisateurs.length === 0 ? (
          <Empty>Aucun utilisateur enregistré.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Identifiant</th>
                  <th>Nom</th>
                  <th>Rôle</th>
                  <th>Entité</th>
                  <th>Statut</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {utilisateurs.map((utilisateur) => (
                  <tr key={utilisateur.id}>
                    <td>{utilisateur.username}</td>

                    <td>
                      {[utilisateur.first_name, utilisateur.last_name]
                        .filter(Boolean)
                        .join(' ') || '—'}
                    </td>

                    <td>{nomRole(utilisateur.role)}</td>

                    <td>
                      {utilisateur.role === 'demandeur'
                        ? nomEntite(utilisateur)
                        : '—'}
                    </td>

                    <td>
                      <span className="badge">
                        {utilisateur.actif ? 'Actif' : 'Désactivé'}
                      </span>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={() => changerStatut(utilisateur)}
                      >
                        {utilisateur.actif ? 'Désactiver' : 'Activer'}
                      </button>
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