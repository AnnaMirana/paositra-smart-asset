import { Link } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { Card, Empty, ErreurChargement, Loading, PageHeader, StatutBadge } from '../components/ui';
import { fmtDate, fmtDateHeure, TYPES_MOUVEMENT } from '../lib/format';
import { useLoad } from '../lib/hooks';
import { peutAutoriser, peutSoumettreRole, peutSortir, peutValider } from '../lib/roles';

function ListeBons({ bons, vide }) {
  if (bons.length === 0) return <Empty>{vide}</Empty>;
  return (
    <div className="table-wrap">
      <table className="table">
        <tbody>
          {bons.slice(0, 8).map((b) => (
            <tr key={b.id}>
              <td>
                <Link to={`/bons-sortie/${b.id}`}>{b.reference_bs}</Link>
              </td>
              <td>{b.entite_nom}</td>
              <td>{fmtDate(b.date_bs)}</td>
              <td className="num">{b.lignes.length} ligne(s)</td>
              <td>
                <StatutBadge statut={b.statut} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {bons.length > 8 && <small>… et {bons.length - 8} autre(s). Voir « Bons de sortie ».</small>}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, loading, error, reload } = useLoad(async () => {
    const [bons, types, mouvements] = await Promise.all([
      api.list('bons-sortie'),
      api.list('types-article'),
      api.list('mouvements'),
    ]);
    return { bons, types, mouvements };
  }, []);

  if (loading && !data) return <Loading />;
  if (error && !data) return <ErreurChargement erreur={error} onRetry={reload} />;

  const { bons, types, mouvements } = data;
  const parStatut = (s) => bons.filter((b) => b.statut === s);
  const sansStock = types.filter((t) => t.quantite_stock === 0).length;

  // Sections « à traiter » : seulement celles qui concernent le rôle de la personne connectée.
  const sections = [];
  if (peutAutoriser(user)) {
    sections.push({ titre: 'À autoriser (DSID)', bons: parStatut('en_attente_autorisation'), vide: 'Aucun bon en attente d’autorisation.' });
  }
  if (peutValider(user)) {
    sections.push({ titre: 'À valider (DCA)', bons: parStatut('en_attente_validation'), vide: 'Aucun bon en attente de validation.' });
  }
  if (peutSortir(user)) {
    sections.push({ titre: 'À sortir (CAME)', bons: parStatut('valide'), vide: 'Aucun bon validé en attente de sortie.' });
  }
  if (peutSoumettreRole(user)) {
    sections.push({
      titre: 'Mes brouillons',
      bons: bons.filter((b) => b.statut === 'brouillon' && (user.is_superuser || b.utilisateur === user.id)),
      vide: 'Aucun brouillon.',
    });
  }

  return (
    <>
      <PageHeader titre={`Bonjour ${user.nom_complet}`} sousTitre={user.role_libelle || 'Tableau de bord'} />

      <div className="grille">
        <div className="kpi">
          <div className="valeur">{parStatut('en_attente_autorisation').length}</div>
          <div className="libelle">Bons en attente d’autorisation</div>
        </div>
        <div className="kpi">
          <div className="valeur">{parStatut('en_attente_validation').length}</div>
          <div className="libelle">Bons en attente de validation</div>
        </div>
        <div className="kpi">
          <div className="valeur">{parStatut('valide').length}</div>
          <div className="libelle">Bons validés, à sortir</div>
        </div>
        <div className="kpi">
          <div className="valeur">{sansStock}</div>
          <div className="libelle">Type(s) d’article sans stock</div>
        </div>
      </div>

      {sections.length === 0 && (
        <Card>
          <Empty>Utilise le menu pour consulter les bons de sortie, le stock et les mouvements.</Empty>
        </Card>
      )}
      <div className="deux-colonnes">
        {sections.map((s) => (
          <Card key={s.titre} titre={s.titre}>
            <ListeBons bons={s.bons} vide={s.vide} />
          </Card>
        ))}
      </div>

      <Card titre="Derniers mouvements" actions={<Link to="/mouvements">Tout voir</Link>}>
        {mouvements.length === 0 ? (
          <Empty>Aucun mouvement pour l’instant.</Empty>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <tbody>
                {mouvements.slice(0, 6).map((m) => (
                  <tr key={m.id}>
                    <td>{fmtDateHeure(m.date_mouvement)}</td>
                    <td>{TYPES_MOUVEMENT[m.type_mouvement] || m.type_mouvement}</td>
                    <td>{m.cible}</td>
                    <td>{m.entite_nom || '—'}</td>
                    <td>{m.utilisateur_nom}</td>
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