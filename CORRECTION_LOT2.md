# PAOSITRA SMART ASSET — Correctif Lot 2

## Décision métier appliquée

- Le DSID et le CAME peuvent créer une entrée de stock.
- Le DSID et le CAME peuvent ajouter les lignes de l'entrée (conformément au droit de créer l'entrée).
- Seul le CAME peut téléverser ou remplacer le document justificatif d'une entrée.
- L'administrateur conserve tous les droits.
- La gestion des référentiels (catégories, types, entités, fournisseurs) reste réservée à l'administrateur.

## Corrections apportées suite aux 6 échecs

1. Les tests de connexion en session fournissent maintenant `nom_agent`, obligatoire pour la traçabilité.
2. Le test CSRF utilise un compte administrateur pour tester une écriture autorisée sans contourner la restriction des référentiels.
3. Les tests du workflow associent le demandeur à exactement une entité.
4. Le test des référentiels vérifie le refus DSID (403), puis vérifie la validation d'unicité avec l'administrateur.
5. Le test d'entrée vérifie que le DSID peut créer l'entrée, que son téléversement de document est refusé, et que le CAME peut téléverser le document.

## Fichiers complets modifiés

- `backend/inventaire/views.py`
- `backend/inventaire/test_auth.py`
- `backend/inventaire/tests.py`

Aucune migration de base de données n'est nécessaire pour ce correctif : il modifie les permissions et les tests, pas le schéma.

## Vérification

La compilation syntaxique Python (`compileall`) a réussi dans l'environnement de préparation. Les tests Django complets n'ont pas été exécutés ici, car Django et les dépendances du projet ne sont pas installés dans cet environnement. Exécuter localement :

```bash
python manage.py test inventaire
```
