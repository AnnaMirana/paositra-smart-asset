utilisateur(0,n) <-> fournisseur (1,1)
            (0,n) <-> entree (1,1)
            (0,n) <-> ligne_entree (1,1)
            (0,n) <-> bon_sortie (1,1)
            (0,n) <-> mouvement (1,1)

Categorie (1,n) <-> type_article (1,1)

type_article(1,n)<->article(1,1)
            (1,n)<->fournisseur(1,n)
            (1,n)<->entree(1,n)
            (1,n)<->bon_sortie(1,n)
            (1,n)<->mouvement(1,n)
            (1,n)<->direction(1,n)

article(1,1)<->categorie(1,n)
        (1,1)<->(1,n) fournisseur
        <!-- (1,1)<->(1,n) entree
        (1,1)<->(1,n) ligne_entree
        (1,1)<->(1,n) bon_sortie
        (1,1)<->(1,n) ligne_sortie --> pour ces 4 la je suis pas sure si c est utilse ou juste avec liaison type_article et et ces 3 entités c'est bon
        (1,n)<->(1,n) mouvement
        (1,1)<->(1,n) direction

fournisseur(1,n)<->(1,n) categorie
            (1,n)<->(1,n) entree
            (1,n)<->(1,n) mouvement

entree(1,n)<->(1,n)categorie
    (1,n)<->(1,1) ligne_entree
    (1,n)<->(0,n) mouvement

categorie(1,n)<->(0,1)ligne_entree

ligne_entree(0,1)<->(1,n) type_article
            (0,n)<->(1,n) article

bon_sortie(1,n)<->(1,n) categorie
            (1,n)<->(1,1) ligne_sortie
            (0,1)<->(1,1) sortie
            (1,1)<->(1,n) direction

sortie(1,1)<->(0,n) utilisateur
        (1,n)<->(0,n) categorie
        (1,n)<->(0,n) type_article
        (1,n)<->(0,1) article
        (1,n)<->(1,1) ligne_sortie
        (1,n)<->(0,n) mouvement
        (1,1)<->(1,n) direction
        
ligne_sortie(1,1)<->(0,n)utilisateur
            (1,1)<->(1,n) categorie
            (0,1)<->(1,n) type_article
            (0,1)<->(1,n) direction

nom précis par ligne de sortie
fichier détail par BS , meme si refusé (lien reference) et suivis par article par reference ou qr code pour accéder au liste de ceux qui sont sorti 
demandeur ne voit pas le stock mais juste ce qui a déjà été sorti pour lui
historique matériel individuel reste mais les consommable  peuvent etre reinitialiser(par an/bouton reset pour admin) 
auditeur peux regarder toutes les historiques par agences , ou en global
demandeur pou upload docc bs, came quand c'est sorti
came seule peut upload les docs pour l entrée
export fichier de l'état pour chaque fichier
entité et demandeur relié 
demandeur remplacé par type_entité
dans l'interface rajouter direct la permission à l'admin de rajouter des catégories , types , etc directement via l'nterface et non dans l'admin django
nom,prenom,matricul pour les logins pour voir les suivis 
pour dsid on laisse mais apres dans dca , on partage en 2 catégories le dsid clique sur qui des dca peux le voir(dga ou dg sinon il peut mettre direct en came et ne passe pas par dca)