import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState
} from 'react';

import { api } from '../api';

import {
    definirGestionnaireNonAutorise,
    messageErreur
} from '../api/client';

const AuthContext = createContext(null);


export function AuthProvider({ children }) {

    const [user, setUser] = useState(undefined);
    const [erreurServeur, setErreurServeur] = useState('');


    // Vérifier la session Django existante.
    const rafraichir = useCallback(async () => {

        try {

            const profil = await api.me();

            setUser(
                profil.authentifie ? profil : null
            );

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


    // Connexion avec identité déclarée.
    const login = useCallback(
        async (username, password, nomAgent) => {

            if (!nomAgent || !nomAgent.trim()) {
                throw new Error(
                    "Le nom et prénom de l'agent sont obligatoires."
                );
            }

            // Transmission des trois informations à Django.
            const profil = await api.login(
                username,
                password,
                nomAgent.trim()
            );

            // Le profil retourné contient le nom de la session.
            setUser(profil);

            setErreurServeur('');

            return profil;

        },
        []
    );


    // Déconnexion.
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
            logout
        }),
        [
            user,
            erreurServeur,
            login,
            logout
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