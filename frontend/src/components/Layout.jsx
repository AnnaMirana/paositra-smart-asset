import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import Logo from './Logo';

const MENU = [
  { to: '/', label: 'Tableau de bord', end: true },
  { to: '/bons-sortie', label: 'Bons de sortie' },
  { to: '/entrees', label: 'Entrées' },
  { to: '/stock', label: 'Stock' },
  { to: '/articles', label: 'Articles' },
  { to: '/mouvements', label: 'Mouvements' },
  { to: '/referentiels', label: 'Référentiels' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [menuOuvert, setMenuOuvert] = useState(false);
  const navigate = useNavigate();

  async function deconnecter() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="app">
      <aside className={`sidebar ${menuOuvert ? 'ouvert' : ''}`}>
        <Logo clair />
        <nav>
          {MENU.map((m) => (
            <NavLink
              key={m.to}
              to={m.to}
              end={m.end}
              onClick={() => setMenuOuvert(false)}
              className={({ isActive }) => `nav-item ${isActive ? 'actif' : ''}`}
            >
              {m.label}
            </NavLink>
          ))}
          {(user.is_staff || user.is_superuser) && (
            <a className="nav-item nav-externe" href="http://127.0.0.1:8000/admin/" target="_blank" rel="noreferrer">
              Administration Django ↗
            </a>
          )}
        </nav>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="btn btn-ghost menu-btn"
            onClick={() => setMenuOuvert((o) => !o)}
            aria-label="Ouvrir le menu"
          >
            ☰
          </button>
          <div className="topbar-user">
            <div className="user-info">
              <strong>{user.nom_complet}</strong>
              <span>{user.role_libelle || (user.is_superuser ? 'Super-utilisateur' : 'Sans rôle')}</span>
            </div>
            <button type="button" className="btn btn-sm" onClick={deconnecter}>
              Déconnexion
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}