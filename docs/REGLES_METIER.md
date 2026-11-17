# Règles métier implémentées et limites

## Produits et conditionnements — phase 2 en cours

Un produit dispose d'une unité de base saisie. Un conditionnement casier, carton,
bouteille, pack ou canette n'existe que si l'utilisateur le configure pour ce produit.
Son coefficient est strictement positif (trois décimales maximum) ; le conditionnement
portant le nom de l'unité de base vaut un. Les quantités de conditionnement sont
entières par défaut ; une fraction doit être explicitement autorisée. La conversion
multiplie la quantité par le coefficient et refuse une précision supérieure à trois
décimales. Prix en FCFA entiers, indépendants par conditionnement ; un prix absent
ne doit pas être proposé comme zéro.

Le stock initial saisi à la création produit un mouvement ; la modification directe
du stock par la fiche produit est interdite. Une unité ne peut pas changer après un
mouvement ou un conditionnement. Exception explicite : pour un produit dont l’unité
historique est `unit`, le propriétaire peut, après vérification et confirmation,
déclarer l’unité réelle sans convertir les quantités. Le motif est enregistré dans
un mouvement de déclaration de quantité nulle ; les historiques ne sont pas réécrits.
Si des unités historiques différentes ou des conditionnements existent, la procédure
est refusée et une analyse manuelle est nécessaire. L'archivage ne
supprime pas les données.

L'import CSV est une création seulement : prévisualisation, références et codes-barres
uniques, catégories déjà présentes, échec global si une ligne est invalide ; le stock
initial importé est tracé. L'export ne comprend que les produits actifs et ne constitue
pas une sauvegarde. Les prix non renseignés des nouveaux produits restent inconnus ;
les anciennes valeurs, y compris zéro, ne sont pas automatiquement réinterprétées.

Les achats, ventes, dettes et rapports de MAJ.md ne sont pas encore raccordés aux
conditionnements et ne sont pas validés. Aucun coût moyen ou bénéfice n'est inventé.

Le coût moyen interne peut être représenté exactement par une fraction de FCFA par
unité. Il est inconnu à la création ou après migration : rien n'est estimé. Le calcul
à la réception est prévu en phase 3. La valorisation exige un coût connu pour tous
les articles en stock et un total entier en FCFA ; aucune fraction n'est arrondie.
