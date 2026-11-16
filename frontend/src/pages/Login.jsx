
import { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { messageErreur } from '../api/client';
import Logo from '../components/Logo';
import { Alert, Field } from '../components/ui';

export default function Login() {
  const { user, login, erreurServeur } = useAuth();
  const location = useLocation();

  const [nom, setNom] = useState('');
  const [password, setPassword] = useState('');
  const [erreur, setErreur] = useState('');
  const [occupe, setOccupe] = useState(false);

  if (user) {
    return (
      <Navigate
        to={
          user.doit_changer_mot_de_passe
            ? '/changer-mot-de-passe'
            : location.state?.from || '/'
        }
        replace
      />
    );
  }

  async function envoyer(e) {
    e.preventDefault();

    setErreur('');
    setOccupe(true);

    try {
      await login(nom.trim(), password);
    } catch (err) {
      setErreur(messageErreur(err));
    } finally {
      setOccupe(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <Logo />

        <h1>Connexion</h1>

        <form onSubmit={envoyer}>
          <Alert type="erreur">
            {erreur || erreurServeur}
          </Alert>

          <Field label="Nom et prénom">
            <input
              type="text"
              value={nom}
              onChange={(e) => setNom(e.target.value)}
              placeholder="Ex. Jean Rakoto"
              autoComplete="name"
              autoFocus
              required
            />
          </Field>

          <Field label="Mot de passe">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </Field>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={occupe}
          >
            {occupe ? 'Connexion…' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
}
