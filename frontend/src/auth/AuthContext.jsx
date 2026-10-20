import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import { definirGestionnaireNonAutorise, messageErreur } from '../api/client';

// user === undefined : on vérifie encore la session ; null : pas connecté ; objet : connecté
// L'objet vient de GET /api/auth/me/ : { id, username, nom_complet, role, role_libelle, is_superuser, ... }
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
    // Si le serveur dit « pas connecté » pendant l'utilisation, on revérifie la session.
    definirGestionnaireNonAutorise(rafraichir);
    rafraichir();
    }, [rafraichir]);

    // AuthContext.jsx (Correction de la ligne 29)
    const login = useCallback(async (username, password) => {
        const profil = await api.login(username, password);
        setUser(profil);
        setErreurServeur('');
        return profil;
    }, []);

    const logout = useCallback(async () => {
        try {
            await api.logout();
        } finally {
            setUser(null);
        }
    }, []);

    const valeur = useMemo(
        () => ({ user, erreurServeur, login, logout }),
        [user, erreurServeur, login, logout],
    );
    return <AuthContext.Provider value={valeur}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    return useContext(AuthContext);
}