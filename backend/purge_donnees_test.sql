
-- PAOSITRA SMART ASSET
-- Purge des données métier de test.
-- CONSERVE les comptes utilisateurs et les tables techniques Django.
-- À exécuter uniquement si les données à supprimer sont bien des données de test.

\echo '--- Vérification avant purge ---'

SELECT 'utilisateurs conservés' AS element, COUNT(*) AS nombre
FROM inventaire_utilisateur
UNION ALL
SELECT 'categories', COUNT(*) FROM inventaire_categorie
UNION ALL
SELECT 'types_articles', COUNT(*) FROM inventaire_typearticle
UNION ALL
SELECT 'fournisseurs', COUNT(*) FROM inventaire_fournisseur
UNION ALL
SELECT 'entites', COUNT(*) FROM inventaire_entite
UNION ALL
SELECT 'articles', COUNT(*) FROM inventaire_article
UNION ALL
SELECT 'entrees', COUNT(*) FROM inventaire_entree
UNION ALL
SELECT 'bons_sortie', COUNT(*) FROM inventaire_bonsortie
UNION ALL
SELECT 'sorties', COUNT(*) FROM inventaire_sortie
UNION ALL
SELECT 'mouvements', COUNT(*) FROM inventaire_mouvement;

BEGIN;

TRUNCATE TABLE
    inventaire_mouvement,
    inventaire_intervient,
    inventaire_lignesortie,
    inventaire_sortie_articles,
    inventaire_sortie,
    inventaire_lignebsortie,
    inventaire_bonsortie,
    inventaire_ligneentree,
    inventaire_entree,
    inventaire_article,
    inventaire_typearticle,
    inventaire_categorie,
    inventaire_fournisseur,
    inventaire_utilisateur_entites,
    inventaire_entite
RESTART IDENTITY CASCADE;

COMMIT;

\echo '--- Vérification après purge ---'

SELECT 'utilisateurs conservés' AS element, COUNT(*) AS nombre
FROM inventaire_utilisateur
UNION ALL
SELECT 'categories', COUNT(*) FROM inventaire_categorie
UNION ALL
SELECT 'types_articles', COUNT(*) FROM inventaire_typearticle
UNION ALL
SELECT 'fournisseurs', COUNT(*) FROM inventaire_fournisseur
UNION ALL
SELECT 'entites', COUNT(*) FROM inventaire_entite
UNION ALL
SELECT 'articles', COUNT(*) FROM inventaire_article
UNION ALL
SELECT 'entrees', COUNT(*) FROM inventaire_entree
UNION ALL
SELECT 'bons_sortie', COUNT(*) FROM inventaire_bonsortie
UNION ALL
SELECT 'sorties', COUNT(*) FROM inventaire_sortie
UNION ALL
SELECT 'mouvements', COUNT(*) FROM inventaire_mouvement;
