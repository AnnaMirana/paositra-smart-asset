
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '../api';
import {
  definirGestionnaireNonAutorise,
  messageErreur,
} from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined);
  const [erreurServeur, setErreurServeur] = useState('');

  const rafraichir = useCallback(async () => {
    try {
      const profil = await api.me();

      setUser(profil.authentifie ? profil : null);
      setErreurServeur('');
    } catch (e) {
      setUser(null);
      setErreurServeur(messageErreur(e));
    }
  }, []);

  useEffect(() => {
    definirGestionnaireNonAutorise(rafraichir);
    rafraichir();
  }, [rafraichir]);

  const login = useCallback(async (nom, password) => {
    if (!nom || !nom.trim() || !password) {
      throw new Error('Le nom et le mot de passe sont obligatoires.');
    }

    const profil = await api.login(nom.trim(), password);

    setUser(profil);
    setErreurServeur('');

    return profil;
  }, []);

  const changerMotDePasse = useCallback(
    async (
      ancien_mot_de_passe,
      nouveau_mot_de_passe,
      confirmation
    ) => {
      const profil = await api.changerMotDePasse({
        ancien_mot_de_passe,
        nouveau_mot_de_passe,
        confirmation,
      });

      setUser(profil);
      return profil;
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const valeur = useMemo(
    () => ({
      user,
      erreurServeur,
      login,
      logout,
      changerMotDePasse,
      rafraichir,
    }),
    [
      user,
      erreurServeur,
      login,
      logout,
      changerMotDePasse,
      rafraichir,
    ]
  );

  return (
    <AuthContext.Provider value={valeur}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
