# DEPOTPRO ERP

Application de bureau professionnelle pour la gestion de dépôt de boissons.

## État actuel

**Version en développement, non prête pour l'exploitation commerciale.** Le module produits est en cours de construction ; les autres écrans
commerciaux historiques sont temporairement masqués pendant leur sécurisation ;
leurs données et leur code sont conservés. Les installations Windows/macOS, le mode
hors ligne complet et la fenêtre native ne sont pas encore validés.

## Installation pour développement

```bash
pip install -r requirements.txt -r requirements-dev.txt
python init_db.py
python main.py
```

Une base neuve ne contient aucun compte ni PIN par défaut. Au premier accès local,
créez et confirmez un PIN de six chiffres. Il est haché et ne chiffre pas la base.
Pour une ancienne base, l'application refuse de démarrer avant la migration manuelle
et la sauvegarde décrites dans `docs/MIGRATIONS.md`. Ne pas exécuter l'ancienne
migration Alembic. Les utilisateurs historiques et leurs relations sont conservés.

## Structure du projet

```
new_depo/
├── main.py                 # Point d'entrée de l'application
├── config.py               # Configuration de l'application
├── database.py             # Configuration de la base de données
├── theme.py                # Thème et styles UI
├── init_db.py              # Script d'initialisation de la BDD
├── models/                 # Modèles SQLAlchemy
├── services/               # Couche de services métier
├── pages/                  # Pages UI de l'application
├── components/             # Composants UI réutilisables
└── requirements.txt        # Dépendances Python
```

## Montants en FCFA

Les montants monétaires sont en francs CFA entiers (XOF), sans arrondi automatique.
Les quantités peuvent rester décimales, mais un total calculé fractionnaire est refusé.
Les nouvelles bases utilisent des colonnes monétaires `INTEGER` ; les valeurs saisies
et lues par SQLAlchemy sont contrôlées. Les taux et les quantités ne sont pas des montants.

Pour une base existante, faites d'abord une sauvegarde cohérente, puis lancez :

```bash
python scripts/audit_fcfa.py /chemin/vers/depot.db
```

Le contrôle est en lecture seule. Corrigez manuellement les éventuels montants
signalés après vérification comptable : ils ne sont jamais arrondis automatiquement.
`create_all` ne modifie pas le schéma existant ; les anciennes colonnes restent en
`NUMERIC` jusqu'à une migration dédiée et testée. Ne pas lancer la migration Alembic
initiale actuelle, qui contient des suppressions de tables.

Pour les tests : `pip install -r requirements.txt -r requirements-dev.txt`,
puis `python -m pytest`.

## Sauvegarde et restauration SQLite

Pour créer une sauvegarde cohérente, même lorsque SQLite utilise le journal WAL :

```bash
python scripts/create_backup.py
```

Les fichiers sont enregistrés dans `~/DepotPro_Data/Sauvegardes`. Pour restaurer,
**arrêtez d'abord DEPOTPRO et tout autre accès à la base**, puis exécutez :

```bash
python scripts/restore_backup.py /chemin/vers/sauvegarde.db --application-arretee
```

La commande vérifie l'intégrité et les tables/colonnes, puis crée une sauvegarde de
la base actuelle avant de la remplacer. La restauration interversions requiert
l'option explicite `--schema-different` : voir `docs/MIGRATIONS.md`. La confirmation d'arrêt est déclarative :
la commande ne peut pas garantir qu'un autre programme n'accède pas à la base.
La restauration depuis l'application est volontairement désactivée. Testez la
procédure sur une copie avant de l'utiliser avec des données importantes.
