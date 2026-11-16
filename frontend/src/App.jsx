
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import Layout from './components/Layout';
import { Loading } from './components/ui';
import Articles from './pages/Articles';
import BonsSortie from './pages/BonsSortie';
import Dashboard from './pages/Dashboard';
import Entrees from './pages/Entrees';
import Login from './pages/Login';
import ChangerMotDePasse from './pages/ChangerMotDePasse';
import Mouvements from './pages/Mouvements';
import Referentiels from './pages/Referentiels';
import Stock from './pages/Stock';
import Utilisateurs from './pages/Utilisateurs';

function Contenu() {
  const { user } = useAuth();

  if (user === undefined) {
    return <Loading texte="Vérification de la session…" />;
  }

  return (
    <Routes>
      <Route path="/changer-mot-de-passe" element={user ? <ChangerMotDePasse /> : <Navigate to="/login" replace />} />

      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />

      <Route
        path="/"
        element={user ? (user.doit_changer_mot_de_passe ? <Navigate to="/changer-mot-de-passe" replace /> : <Layout />) : <Navigate to="/login" replace />}
      >
      
        <Route index element={<Dashboard />} />
        <Route path="bons-sortie" element={<BonsSortie />} />
        <Route path="entrees" element={<Entrees />} />
        <Route path="stock" element={<Stock />} />
        <Route path="articles" element={<Articles />} />
        <Route path="mouvements" element={<Mouvements />} />
        <Route path="referentiels" element={<Referentiels />} />
        <Route
          path="utilisateurs"
          element={
            user && (user.role === 'admin' || user.is_superuser)
              ? <Utilisateurs />
              : <Navigate to="/" replace />
          }
        />
      </Route>

      <Route
        path="*"
        element={<Navigate to={user ? '/' : '/login'} replace />}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Contenu />
      </AuthProvider>
    </BrowserRouter>
  );
}
