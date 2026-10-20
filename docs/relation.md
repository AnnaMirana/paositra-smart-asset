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