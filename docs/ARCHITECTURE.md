# Architecture DEPOTPRO — cible et état

## État actuel

NiceGUI appelle des services SQLAlchemy sur une base SQLite locale. Le routage et
la session sont actuellement globaux, et le modèle est encore multi-utilisateur.
Ce n'est pas l'architecture finale et l'application n'est pas prête à exploiter.

## Cible

- Fenêtre native mono-propriétaire, serveur HTTP lié uniquement à `127.0.0.1` ;
  ressources locales, cycle de vie et verrouillage d'instance à tester.
- Interface sans calcul métier critique : formulaires, listes, confirmations ;
  services indépendants de NiceGUI avec unité de travail et transactions uniques.
- SQLite local, clés étrangères et WAL, migrations versionnées après sauvegarde
  vérifiée ; jamais de migration silencieuse ni d'initialisation destructive.
- Unités de base et conditionnements par produit ; conversion mémorisée sur les
  lignes historiques. Aucune conversion ou prix inventé.
- Paiements et contre-écritures comme écritures de référence, liées à une seule
  vente/dette et aux mouvements de trésorerie ; reporting distinct des encaissements.
- Prix et sommes en FCFA entiers ; Decimal pour les calculs de quantité et coûts
  intermédiaires. Une fraction de FCFA est refusée selon la décision prise dans
  cette conversation, sans arrondi implicite. Les taux ne sont pas des montants.
- Historique non destructif ; conservation des données et relations historiques
  même après retrait des interfaces multi-rôles.
- Sauvegardes via l'API SQLite ; restauration après arrêt complet et confirmation.

## Étapes

L'ordre est celui de `MAJ.md`. Ne pas passer aux conditionnements tant que les
fondations (migrations sûres, premier démarrage, sécurité et tests) sont bloquantes.

## Phase 1 — implémentation partielle

Le propriétaire est authentifié par `OwnerAuthService` et `owner_security` ; les
sessions d'authentification sont courtes et l'état d'interface est propre au client.
La migration manuelle sauvegarde avant suppression logique des anciens PIN ; les
relations historiques des utilisateurs sont conservées. Aucun rôle n'est exposé.
Les écrans commerciaux historiques sont masqués provisoirement, pas supprimés.
Le verrouillage sur inactivité et le serveur localhost sont implémentés, mais un
test interactif navigateur et les tests desktop/hors ligne restent nécessaires.

## Phase 2 — produits et conditionnements

`ProductPackaging` conserve les tarifs entiers facultatifs, l'unité de base et le
coefficient propre au produit ; aucune équivalence n'est initialisée automatiquement.
`PackagingService` contrôle les coefficients, les fractions autorisées et les
codes-barres. `ProductService` trace le stock initial et interdit la modification
directe du stock et les changements d'unité en présence d'un historique.
L'import CSV est entièrement refusé si une ligne est invalide. La conversion n'est
pas encore reliée aux achats et ventes : ces parcours restent masqués.
