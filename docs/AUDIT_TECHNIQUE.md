# Audit technique DEPOTPRO — état au 17 novembre 2026

## Périmètre et méthode

Relevé statique de tous les fichiers Python du dépôt : modèles, services, pages,
composants, PDF, scripts, tests, initialisation, configuration et migration ;
inventaire AST des classes, appels et boutons sans `on_click` ; lecture ciblée des
flux critiques. Installation des dépendances épinglées dans un environnement Python
3.11 Linux, `pip check`, import de `main` et tests pytest. L'analyse statique ne
prouve pas le comportement de chaque dialogue. Pas de tests UI ni Windows/macOS.
Les modifications préexistantes de cette branche sont prises en compte.

## Contexte d'exploitation

Branche de travail Arena active ; base théorique `~/DepotPro_Data/depot.db`
(`config.py`), hors dépôt. **Aucun fichier depot.db n'est présent dans cet
environnement au moment de l'audit** : aucune base commerciale n'a été modifiée
ou sauvegardée. Les tests utilisent des bases temporaires en mémoire/fichiers.
Clés étrangères, WAL et délai de verrouillage sont configurés dans `database.py`.
`create_all` ne migre pas les bases existantes. L'ancienne révision Alembic,
contenant des `DROP TABLE` dans `upgrade`, a été explicitement bloquée ;
`alembic.ini` pointe vers un chemin personnel obsolète et Alembic n'est pas dans
les dépendances. Aucune migration fonctionnelle ne doit être supposée disponible.

## Priorités et remédiations

| Priorité | Constat vérifiable | Remédiation |
|---|---|---|
| P0 | `main.py` partage session, utilisateur et éléments UI globaux ; `init_db.py` crée un compte connu ; `User.pin_code` est en clair et le login affiche `0000`. | Refaire initialisation mono-propriétaire, PIN bcrypt à 6 chiffres, temporisation, sessions isolées et retrait des identifiants par défaut. Migrer les données après sauvegarde. |
| P0 | Migration historique destructrice ; `create_all` n'actualise pas les colonnes. | Nouvelle chaîne versionnée, sauvegarde SQLite vérifiée, détection des schémas et essais sur copies, puis contrôle d'intégrité. Ne pas appliquer l'ancienne révision. |
| P0 | `pages/new_sale.py` utilise `SaleStatus.COMPLETED`, `Product.sale_price`, `Product.consignment` inexistants et appelle `create_sale` sans lignes ; le panier n'est pas relié aux lignes du tableau. | Refaire le parcours après les modèles conditionnement et transaction de vente. |
| P0 | Paiements répartis entre `SalesService`, `PaymentService` et `DebtService` ; les champs vente/dette/client/caisse ne sont pas synchronisés ; `client.balance` n'existe pas (`financial_balance`). | Source de vérité unique pour les paiements, créances et mouvements ; écritures atomiques et contrepassations. |
| P0 | `CashService` ajoute également Mobile Money au solde théorique physique ; plusieurs sessions possibles et pas de lien automatique aux paiements. | Journal de mouvements par moyen, session unique, calculs séparés et tests. |
| P0 | `PurchaseService` ne borne pas les réceptions par solde ; une réception ne met pas à jour dettes ni coût moyen ; les transactions sont seulement partiellement durcies. | Réceptions identifiées, contrôlées, atomiques, gestion de la conversion et coût historique. |
| P1 | `Product` n'a pas de `ProductPackaging`, conversion par produit, coût moyen ni règle de fractions des conditionnements. `update_product` peut modifier silencieusement le stock. | Modèle et service de conditionnement, stock centralisé et mouvements exclusifs. |
| P1 | `pages/dashboard.py` appelle `get_dashboard_kpis` et `get_sales_trend`, absents de `ReportingService` ; signature des meilleurs produits différente. `ReportingService` utilise entre autres `Sale.sale_date`, `Sale.status`, `Product.sku` et `Client.balance` inexistants. | Rapports testés contre les modèles et indicateurs calculés sur les écritures réelles. |
| P1 | `ExpenseService` utilise `Expense.expense_date` absent (`date`) ; `cash_closure_service.py` importe `CashRegister` et `CashClosure` inexistants ; consignations utilisent des champs différents de leur modèle ; `BusinessRulesService` utilise `Settings.key/value` inexistants. | Corriger ou remplacer les services après analyse des historiques ; tests par parcours. |
| P1 | Nombreux boutons sans action : caisse 4/4, rapports 4/4, paramètres 5/5, produits 1/1 ; d'autres pages similaires. `settings` appelle des méthodes absentes. Certains `pass` dans dashboard et stock. | Refaire progressivement les écrans, retirer les actions non disponibles et tester chaque bouton. |
| P1 | Références produits et ventes basées sur la seconde ; collision possible. | Génération unique et transactionnelle. |
| P1 | Sauvegarde par API SQLite et restauration hors ligne introduites sur la branche ; pas de sauvegarde quotidienne ni interface ; restauration exige schémas identiques, comparaison limitée aux noms de tables/colonnes. | Tests de reprise, migration et compatibilité, orchestration hors ligne, UI et surveillance ; ne pas promettre la validation complète d'un schéma. |
| P1 | FCFA entier contrôlé à l'écriture et lecture ORM, mais anciennes colonnes NUMERIC non migrées ; requêtes SQL directes peuvent contourner les contrôles ; des calculs de rapports peuvent encore être fractionnaires. | Migration contrôlée et contraintes DB ; cohérence des calculs et refus des fractions selon décision utilisateur. |
| P2 | `main.py` lance NiceGUI en mode navigateur, pas de chaîne native/arrêt vérifiée ; données sous `~/DepotPro_Data` sur tous systèmes ; pas de build PyInstaller. | Démarrage local natif, chemins adaptés et migration explicite des données, tests sur les OS cibles. |
| P2 | Dépendances épinglées : NiceGUI 1.4.0, SQLAlchemy 2.0.23, bcrypt 4.0.1, pywebview 4.4.1, pandas 2.1.3, ReportLab 4.0.7 ; python-dotenv déclaré, pas d'usage trouvé. Alembic et PyInstaller absents. | Audit de sécurité et compatibilité avant mises à jour ; ne pas supprimer sans tests ; tester ressources hors ligne. |

## Cartographie

- `models/` : catégories/produits, clients, fournisseurs, mouvements stock,
  ventes/lignes, commandes/lignes, paiements, dettes, consignations/lignes,
  livraisons, dépenses, caisse/mouvements, rôles/utilisateurs/permissions,
  paramètres. Aucun modèle de conditionnement.
- `services/` : services CRUD de ces domaines ; règles métier séparées mais non
  appelées dans le flux de vente ; clôture et rapports en partie incompatibles
  avec les modèles. Les suppressions de dettes/paiements/consignations sont
  contraires à l'exigence de traçabilité et doivent être revues.
- `pages/` : 19 pages, pour la plupart connectées en lecture partielle mais non
  prouvées opérationnelles ; décalages entre leurs appels et les services.
- `components/` : navigation de 18 modules y compris utilisateurs et rôles,
  en-tête avec action non reliée.
- `pdf/` : facture, reçu, commande, livraison et clôture présents ; intégration
  aux transactions et exactitude des champs à vérifier.
- `validation.py`, `money.py` : validation générique et contrôle entier FCFA ;
  les quantités restent en Decimal. `scripts/` : audit monétaire et sauvegarde/
  restauration hors ligne. `utils/permissions.py` concerne le modèle multi-rôle.

## Vérifications et limites

- Python 3.11.2 Linux : dépendances `requirements.txt` installées, `pip check` OK,
  `import main` OK. Cela ne vérifie ni les parcours UI ni les plateformes cibles.
- Suite : 36 tests réussis à l'audit ; tests stock/monnaie/sauvegarde inclus,
  mais scénarios métier A–J de `MAJ.md` largement absents.
- Pas de test d'exécution hors ligne, de fenêtre native ou de build. Aucun paquet
  Windows/macOS généré ou validé. Versions de dépendances non auditées pour CVE.
- La phase 0 ne prétend pas certifier toutes les interactions dynamiques. Les
  écarts ci-dessus bloquent la validation des fondations et l'usage en production.
