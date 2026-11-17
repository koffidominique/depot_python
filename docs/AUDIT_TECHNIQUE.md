# Audit technique DEPOTPRO — phase 0 actualisée

## Périmètre et méthode

Audit du 17 novembre 2026, branche `arena/be170884-depot-python`, à partir du
commit `6b2c96246fbeb5dbaf3fbaf917f7ed9834a734a0` de `main`. Inventaire des
fichiers suivis, inspection des modèles, pages, services, migrations, scripts,
documentation et dépendances ; imports des modules dans un HOME temporaire ;
lecture ciblée des parcours et exécution des tests. L'inspection statique et les
tests ne prouvent pas toutes les interactions ni la sécurité en exploitation.
Cet audit remplace le diagnostic initial devenu obsolète sans supprimer les
étapes historiques consignées dans `docs/CHANGELOG.md` et `docs/TESTS.md`.

L'application est **en développement, non prête pour la production**. Aucun
fichier `~/DepotPro_Data/depot.db` n'était présent au début de cet audit ; aucune
base commerciale n'a été lue, modifiée, migrée ou sauvegardée. L'import de
`config.py` crée toutefois des dossiers locaux. Les tests utilisent des bases de
test. Les données utilisateur et sauvegardes existantes ailleurs ne sont pas
couvertes par cet audit.

## Cartographie actuelle

- 141 fichiers suivis ; 23 fichiers Python de modèles, 31 de services, 23 de
  pages, 2 de composants, 6 PDF, 4 scripts, 21 de tests et 2 de migration.
- `main.py` expose les pages tableau de bord provisoire, produits, stocks,
  emballages, approvisionnements, ventes au comptant, caisse et sécurité. Les
  pages historiques restent dans le dépôt mais ne sont pas raccordées au menu.
- Authentification : `pages/login.py` → `OwnerAuthService` → `owner_security` ;
  PIN bcrypt à six chiffres, temporisation persistante, état UI par client.
- Produits : `pages/products.py` → services produit, conditionnement, CSV et
  image ; `ProductPackaging` représente une conversion explicite par produit.
- Approvisionnements : `pages/purchases_phase3.py` → `PurchaseService` et
  `SupplierPaymentService` ; réception et mouvement stock, dette par réception,
  règlement lié à une session de caisse pour les nouveaux paiements.
- Stock : `pages/stock.py` → inventaires et corrections ; emballages vides :
  `pages/returnable_packaging.py` → catalogue et journal manuel séparés.
- Vente au comptant : `pages/managed_sales.py` → `ManagedSaleService` →
  `ManagedSale`, lignes, stock et `ManagedCashTransaction` dans une transaction.
  `pages/managed_cash.py` → `ManagedCashService` ; les flux fournisseurs utilisent
  `ManagedCashEntry`, les autres flux `ManagedCashTransaction`.
- Données historiques : `Sale`, `Payment`, `Expense`, `CashSession` et services
  associés coexistent avec les modèles `Managed*` ; les historiques ne sont pas
  automatiquement rapprochés, et les anciens rapports ne couvrent pas les nouvelles
  ventes. `pdf/` contient des générateurs anciens, intégration non démontrée.
- SQLite : `config.py` pointe vers `~/DepotPro_Data/depot.db` ; `database.py`
  configure clés étrangères, WAL et délai d'attente. `scripts/migrate_database.py`
  prévoit les versions 1 à 17, avec sauvegarde vérifiée et transaction, après arrêt.
  `create_all` ne migre pas les bases existantes. La révision Alembic initiale
  destructive est bloquée ; `alembic.ini` conserve un chemin personnel obsolète.

## Constats classés et solutions

| Priorité | Constat actuel et conséquence | Solution / phase |
|---|---|---|
| P0 | L'ancien circuit `Sale`/`Payment` et le circuit `ManagedSale`/caisse coexistent sans source financière unifiée. Les rapports historiques ne comptent pas les nouvelles ventes ; les paiements historiques ne sont pas rapprochés. | Maintenir les écrans historiques masqués ; définir une source de vérité, une stratégie explicite et non destructive de rapprochement, puis tester ventes/dettes/caisse de bout en bout (phases 4–7). |
| P0 | Crédit client, retours, remboursements et contrepassations manquent dans le parcours actif ; le paiement mixte existe uniquement pour les ventes au comptant intégralement réglées. Les opérations commerciales ne sont pas terminées. | Implémenter les écritures atomiques, liens et contre-écritures avant exposition et tester les scénarios C–G (phases 4–5). |
| P0 | Le catalogue des vides n'est pas relié aux produits : un produit à consigne positive connue est refusé à la vente, mais une consigne inconnue ne peut pas être détectée automatiquement. Les mouvements de vides sont manuels et ne calculent pas les dettes clients. | Modéliser explicitement emballage, compatibilité et soldes, sans inventer de valeurs ; lier mouvements et contreparties de manière transactionnelle avant exploitation (phase 5). |
| P0 | La caisse distingue les flux par moyen, mais ne gère pas les soldes non espèces, transferts et rapprochements ; les mouvements manuels peuvent répéter une opération commerciale déjà enregistrée. | Journal unifié, références métier uniques, comptes et contrôles d'ouverture/clôture par moyen, tests de non-double comptabilisation (phases 4–6). |
| P0 | Une base commerciale réelle et son schéma ne sont pas disponibles pour cet audit ; le contrôle d'intégrité SQLite et la comparaison de tables/colonnes ne valident pas toutes les contraintes ou données métier. Les anciens montants `NUMERIC` ne sont pas convertis. | Sauvegarder base et images, auditer les montants en lecture seule et tester la migration et la restauration sur une copie représentative avant tout usage ; ne pas convertir automatiquement les fractions (phase 1). |
| P1 | `services.business_rules_service` ne s'importe pas (`datetime` non défini dans une annotation) ; `services.cash_closure_service` ne s'importe pas (`CashRegister` absent). Ces modules historiques ne sont pas sur le menu actif. | Corriger ou remplacer lors des phases concernées, avec tests d'import et de parcours, sans réactiver les anciens écrans en l'état. |
| P1 | `pages/new_sale.py` utilise `Product.sale_price`, `Product.consignment` et `SaleStatus.COMPLETED` absents, et appelle `SalesService.create_sale` sans lignes. `pages/dashboard.py` appelle des méthodes absentes ; `ReportingService` et `ExpenseService` référencent des colonnes inexistantes. | Refaire ou retirer les appels historiques après tests ; développer les rapports sur les écritures réelles, y compris `Managed*` (phases 4, 6 et 7). |
| P1 | Les clés de déduplication existent au niveau de plusieurs services, mais les dialogues créent une nouvelle clé à chaque ouverture : une reprise après interruption n'est pas démontrée idempotente. | Conserver l'identité d'opération jusqu'à résolution et tester double clic, reconnexion et reprise après échec (phases 3–6). |
| P1 | Sauvegarde SQLite via API avec WAL ; images hors base non incluses. Restauration hors ligne contrôlant intégrité et noms de tables/colonnes, pas l'ensemble des contraintes ; pas de sauvegarde quotidienne automatique. | Sauvegarde cohérente base + images, restauration testée sur copie, et documentation de ses limites (phases 1 et 9). |
| P1 | Le PIN ne chiffre pas les fichiers ; récupération après oubli non définie ; migration 2 efface logiquement les anciens PIN mais les sauvegardes ou blocs SQLite peuvent les conserver. | Protéger les fichiers et sauvegardes, définir une récupération sans code universel et vérifier sur copies (phase 1). |
| P1 | `README.md`, `docs/ARCHITECTURE.md` et plusieurs sections historiques de `docs/TESTS.md`/`docs/DECISIONS_A_VALIDER.md` décrivent un état dépassé. | Mettre à jour les vues d'état actuelles sans effacer l'historique, documenter tests, commandes et limites (phases concernées et 9). |
| P2 | `main.py` démarre NiceGUI dans un navigateur sur `127.0.0.1`, sans chaîne d'empaquetage native validée ; aucun installateur Windows/macOS détecté. | Tester mode natif, arrêt et verrouillage d'instance, hors ligne et builds sur les plateformes cibles (phases 8–10). |
| P2 | `python-dotenv`, `pandas` et `pywebview` sont déclarés mais aucune importation directe n'a été trouvée dans les fichiers Python suivis ; Alembic est référencé mais non déclaré. | Vérifier usages indirects, besoins desktop et dépendances transitives avant retrait ou mise à jour ; ne pas supprimer sur cette seule recherche (phases 1 et 8). |

## Validations de cet audit

- Linux, Python 3.11.2 ; environnement virtuel temporaire installé avec
  `requirements.txt` et `requirements-dev.txt` ; `pip check` : aucune dépendance
  incompatible signalée. NiceGUI 1.4.0, SQLAlchemy 2.0.23, bcrypt 4.0.1,
  FastAPI 0.104.1, Starlette 0.27.0, Pillow 11.3.0 ; pytest 8.4.2 installé.
- `python -m pytest -q --tb=short` : **110 réussis, 7 ignorés**, un avertissement
  SQLAlchemy. Les sept tests navigateur exigent `DEPOTPRO_BROWSER`, non configuré
  dans cet environnement ; ils ne sont pas considérés comme passés ici.
- Import individuel des modules `models`, `services`, `pages`, `components` et
  `pdf` : deux échecs cités ci-dessus ; il ne s'agit pas de parcours UI exécutés.
  `compileall` réussit, ce qui ne détecte pas ces erreurs d'import.
- Aucun test de fenêtre native, fonctionnement réellement hors ligne, installation
  ou build Windows/macOS. Pas d'audit CVE des versions épinglées. Les scénarios
  A–J de `MAJ.md` ne sont pas tous couverts.

## Ordre de reprise

La phase 0 donne ce diagnostic ; les fonctions existantes ne sont pas déclarées
validées par simple présence. Reprendre par la phase 1 et ses tests de fondation,
puis phases 2–10 dans l'ordre de `MAJ.md`, en conservant les travaux antérieurs,
en traitant les anomalies bloquantes avant d'exposer les fonctionnalités et sans
modifier les données d'une base réelle sans sauvegarde et essai sur copie.

## Complément de validation des fondations

Après cet audit, les sept parcours navigateur ont été réexécutés avec Chromium
headless sous Linux : suite complète 121 tests réussis. Les contrôles du démarrage
et du changement de PIN ont été renforcés ; les détails et limites sont dans
`TESTS.md` et `ARCHITECTURE.md`. Les risques commerciaux et la nécessité d'auditer
une copie représentative de toute base existante restent inchangés.

## Complément de reprise produits

Les écritures des services produit, conditionnement et import CSV sont sérialisées
avant contrôle des codes-barres. La migration 11 ajoute des protections inter-tables
pour les insertions et modifications SQL directes ; le CSV reste partiel et les
conditionnements restent modifiables.
Les résultats et limites de validation figurent dans `TESTS.md` et `ARCHITECTURE.md`.

## Complément annulations

Une annulation intégrale des nouvelles ventes au comptant (un ou plusieurs
moyens) est maintenant disponible, sous les réserves de `ARCHITECTURE.md`. Les
crédits, consignes intégrées et retours partiels restent des chantiers ouverts ;
l'annulation ne doit pas être assimilée à leur prise en charge.

## Complément crédit

Un premier circuit séparé de crédit et règlements est disponible pour les nouveaux
clients, avec acompte éventuellement mixte. Il n'intègre pas les anciens soldes,
les consignes, les retours ou annulations de crédit. Voir `ARCHITECTURE.md`.

## Complément retours et annulations de crédit

L'annulation totale du nouveau circuit prend désormais en charge le crédit et
les règlements mixtes ; les retours partiels sont disponibles avec répartition
explicite entre remboursement et créance. Ils ne prennent pas en charge les
consignes et ne corrigent pas les historiques antérieurs. Voir `ARCHITECTURE.md`.

## Complément contrepassation des retours

Un retour peut désormais être contrepassé après confirmation du départ des biens
et de la récupération effective des remboursements, avec restrictions sur les
mouvements de stock ultérieurs. Une vente peut être annulée après un retour
partiel par retour du reliquat et extinction explicite des contreparties. Les
consignes ne sont toujours pas intégrées ; voir `ARCHITECTURE.md`.

## Préparation des consignes

La composition des emballages peut être configurée explicitement par
conditionnement, et une configuration inconnue ne permet plus une vente. Les
ventes consignées sont également bloquées : les écritures commerciales et
physiques ne sont pas encore réalisées. Voir `ARCHITECTURE.md`.

### Mise à jour v18

Le nouveau circuit accepte les ventes consignées et les retours de vides avec écritures client, stock de vides et contreparties financières liées. Il ne raccorde pas les historiques. Annulation de vente consignée, retour de marchandise consignée et annulation de retour de vides restent indisponibles ; déclarer le stock initial de vides avant retour. Les limitations relatives aux versions précédentes restent historiques.

Mise à jour : le retour de marchandise consignée est maintenant ouvert séparément du retour de vides, avec contrôle financier partagé. Les annulations totales de ventes consignées et de retours de vides demeurent bloquées. Le rapprochement historique manuel reste à développer.

Mise à jour v20 : annulation d'un retour de vides et annulation totale d'une vente consignée sans retour actif sont désormais disponibles sous les contrôles indiqués dans le changelog. Les retours actifs doivent être annulés d'abord, et peuvent eux-mêmes être bloqués en présence de mouvements de stock ultérieurs. La reprise manuelle des soldes historiques confirmée par l'utilisateur reste non implémentée.
