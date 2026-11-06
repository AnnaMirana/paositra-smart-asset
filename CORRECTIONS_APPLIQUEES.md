# PAOSITRA SMART ASSET — version corrigée (lot 1)

Cette archive contient le projet complet, avec les fichiers source modifiés et les fichiers non modifiés conservés. Les dossiers `node_modules`, `venv`, `.git`, `dist`, les caches Python et le fichier privé `backend/.env` ne sont pas inclus.

## Modifications intégrées

- Ajout de vrais champs de fichiers pour le justificatif d'entrée, le justificatif du Bon de Sortie et la preuve de livraison physique.
- La preuve de livraison du CAME est obligatoire pour enregistrer une sortie physique depuis l'API.
- Les fichiers acceptés sont PDF, JPG, JPEG et PNG, avec une limite de 10 Mo.
- Stockage local des fichiers dans `backend/media/documents/`.
- Permissions backend : écriture des catégories/types/fournisseurs/entités réservée à l'administrateur ; entrées enregistrées par le CAME ou l'administrateur ; demandeur limité à ses propres bons et aux mouvements de son entité ; CAME limité aux bons validés/sortis ; auditeur en lecture seule avec filtre d'entité possible.
- Un compte Demandeur doit être associé à exactement une entité. L'administrateur peut modifier ce rattachement dans Référentiels > Comptes / entités.
- Ajout de l'interface de création des entités, catégories, types d'articles et fournisseurs.
- Ajout des routes d'export Excel et PDF sur les principaux référentiels, listes et historiques.
- Conservation des anciens champs texte `document` pour ne pas casser les données déjà enregistrées.

## Installation / remplacement

1. Fais une copie de sauvegarde de ton dossier actuel et une sauvegarde PostgreSQL avant remplacement.
2. Décompresse cette archive dans un nouveau dossier. Ne supprime pas ton ancien dossier avant d'avoir vérifié le nouveau.
3. Recrée `backend/.env` à partir de `backend/.env.example` et remets tes propres paramètres PostgreSQL et `DJANGO_SECRET_KEY`. Le fichier `.env` privé n'est volontairement pas dans l'archive.
4. Dans un terminal, ouvre `backend` puis installe les dépendances :

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py check
   python manage.py test inventaire
   python manage.py runserver
   ```

5. Dans un deuxième terminal, ouvre `frontend` puis installe et lance React :

   ```bash
   npm install
   npm run dev
   ```

6. Le frontend Vite reste configuré sur `http://localhost:3000`, avec proxy vers Django sur `http://127.0.0.1:8000`.

## Migration et fichiers

La migration `inventaire.0008_documents_fichiers` ajoute trois colonnes de fichiers sans supprimer les anciennes valeurs texte. Les anciens documents déjà stockés sous forme de texte ne sont pas convertis automatiquement en fichiers : il faudra les téléverser à nouveau si les fichiers originaux existent.

Les documents téléversés sont stockés dans `backend/media/` et leur consultation passe par des routes API authentifiées. Ne configure pas de serveur web qui expose directement le dossier `media/` publiquement.

## Vérifications réalisées ici

- Compilation syntaxique Python (`py_compile`) des fichiers backend modifiés : réussie.
- Vérification syntaxique JavaScript/JSX : réussie avant la réinstallation locale des dépendances.
- Le build Vite complet et les tests Django n'ont pas pu être exécutés dans cet environnement : le ZIP initial contenait des dépendances Node compilées pour Windows, non exécutables dans l'environnement Linux, et Django n'est pas installé dans l'environnement d'exécution ici. Ils doivent être exécutés avec les commandes ci-dessus sur ton ordinateur.

## Point volontairement reporté

Le changement d'affichage « Demandeur » vers le type d'entité n'est pas inclus. Il reste à faire en dernier, après tes consignes précises, sans modifier le rôle métier `demandeur`.
