import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { messageErreur } from '../api/client';
import Logo from '../components/Logo';
import { Alert, Field } from '../components/ui';

export default function ChangerMotDePasse() {
  const { user, changerMotDePasse, logout } = useAuth();
  const [ancien, setAncien] = useState('');
  const [nouveau, setNouveau] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [erreur, setErreur] = useState('');
  const [occupe, setOccupe] = useState(false);

  if (!user) return <Navigate to="/login" replace />;
  if (!user.doit_changer_mot_de_passe) return <Navigate to="/" replace />;

  async function envoyer(e) {
    e.preventDefault();
    setErreur('');
    setOccupe(true);
    try {
      await changerMotDePasse(ancien, nouveau, confirmation);
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
        <h1>Créer votre mot de passe</h1>
        <p>Votre première connexion nécessite le remplacement du mot de passe temporaire.</p>
        {erreur && <Alert type="erreur">{erreur}</Alert>}
        <form onSubmit={envoyer}>
          <Field label="Mot de passe temporaire reçu par e-mail">
            <input type="password" value={ancien} onChange={e => setAncien(e.target.value)} autoComplete="current-password" required />
          </Field>
          <Field label="Nouveau mot de passe">
            <input type="password" value={nouveau} onChange={e => setNouveau(e.target.value)} autoComplete="new-password" minLength={8} required />
          </Field>
          <Field label="Confirmer le nouveau mot de passe">
            <input type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" minLength={8} required />
          </Field>
          <button className="btn btn-primary" type="submit" disabled={occupe}>{occupe ? 'Enregistrement…' : 'Valider mon nouveau mot de passe'}</button>
          <button className="btn" type="button" onClick={logout}>Se déconnecter</button>
        </form>
      </div>
    </div>
  );
}
