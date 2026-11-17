"""Infrastructure de migrations DEPOTPRO, à exécuter application arrêtée.

Les versions 1–20 couvrent l'historique, la sécurité locale, les conditionnements,
le stockage exact du coût moyen et les structures de réception et inventaire. Les montants existants ne sont pas convertis.
"""
import argparse
import sqlite3
from contextlib import closing
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH
from database import Base
import models  # enregistre les tables avant la vérification du schéma

VERSION = 20
from services.barcode_constraints import TRIGGERS, verify_barcode_constraints


def _verify(connection):
    if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Échec du contrôle d’intégrité SQLite.')
    if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
        raise ValueError('Clés étrangères incohérentes : aucune migration appliquée.')


def migrate(path: Path) -> Path | None:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Base introuvable : {path}')
    backup = path.with_name(f'{path.stem}_avant_migration_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}.db')
    with closing(sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=5, isolation_level=None)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')  # Empêche d'autres écritures durant la sauvegarde et la migration.
        try:
            _verify(db)
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'products', 'sales', 'users'}.issubset(tables):
                raise ValueError('Ce fichier ne contient pas les tables DEPOTPRO attendues.')
            # Aucune hypothèse sur un schéma partiel ou provenant d'une autre version.
            for table in Base.metadata.sorted_tables:
                if table.name in ('owner_security', 'product_packagings', 'inventories', 'inventory_lines', 'purchase_receipts', 'purchase_receipt_lines', 'returnable_packaging_types', 'returnable_stock_balances', 'returnable_stock_movements', 'managed_cash_sessions', 'managed_cash_entries', 'managed_sales', 'managed_sale_lines', 'managed_cash_transactions', 'managed_sale_payments', 'managed_sale_cancellations', 'managed_sale_refunds', 'managed_credit_profiles', 'managed_credit_sales', 'managed_credit_payments', 'managed_returns', 'managed_return_lines', 'managed_return_refunds', 'managed_return_cancellations', 'managed_return_recaptures', 'deposit_packaging_profiles', 'deposit_packaging_components', 'managed_deposit_issues', 'managed_deposit_returns', 'managed_deposit_refunds', 'payment_methods', 'managed_deposit_return_cancellations', 'managed_deposit_return_recaptures'):
                    continue
                if table.name not in tables:
                    raise ValueError(f'Schéma DEPOTPRO incompatible : table {table.name} absente.')
                columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table.name}")')}
                expected_columns = {column.name for column in table.columns}
                if table.name == 'products':
                    expected_columns -= {'average_cost_numerator', 'average_cost_denominator'}
                if table.name == 'purchase_order_lines':
                    expected_columns -= {'packaging_id', 'packaging_name', 'base_unit', 'conversion_factor', 'allow_fraction', 'unit_discount', 'unit_fee'}
                if table.name == 'supplier_debts':
                    expected_columns -= {'receipt_id'}
                if table.name == 'payments':
                    expected_columns -= {'cash_link_status'}
                missing = expected_columns - columns
                if missing:
                    raise ValueError(f'Schéma DEPOTPRO incompatible : colonnes absentes dans {table.name} : {sorted(missing)}')
            versions = []
            if 'depotpro_schema_migrations' in tables:
                versions = [row[0] for row in db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version')]
                if versions not in [list(range(1, v + 1)) for v in range(1, VERSION + 1)]:
                    raise ValueError('Historique de migration non reconnu : intervention nécessaire.')
                required = {}
                if 2 in versions:
                    required['owner_security'] = {'id', 'pin_hash', 'failed_attempts', 'locked_until', 'inactivity_seconds'}
                if 3 in versions:
                    required['product_packagings'] = {column.name for column in Base.metadata.tables['product_packagings'].columns}
                if 4 in versions:
                    required['products'] = {'average_cost_numerator', 'average_cost_denominator'}
                if 5 in versions:
                    for name in ('inventories', 'inventory_lines', 'purchase_receipts', 'purchase_receipt_lines'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                    required['purchase_order_lines'] = {'packaging_id', 'packaging_name', 'base_unit', 'conversion_factor', 'allow_fraction'}
                if 6 in versions:
                    required['purchase_order_lines'] |= {'unit_discount', 'unit_fee'}
                    required['supplier_debts'] = {'receipt_id'}
                    required['payments'] = {'cash_link_status'}
                if 7 in versions:
                    required['returnable_packaging_types'] = {column.name for column in Base.metadata.tables['returnable_packaging_types'].columns}
                if 8 in versions:
                    for name in ('returnable_stock_balances', 'returnable_stock_movements'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 9 in versions:
                    for name in ('managed_cash_sessions', 'managed_cash_entries'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 10 in versions:
                    for name in ('managed_sales', 'managed_sale_lines', 'managed_cash_transactions'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 12 in versions:
                    required['managed_sale_payments'] = {column.name for column in Base.metadata.tables['managed_sale_payments'].columns}
                if 13 in versions:
                    for name in ('managed_sale_cancellations', 'managed_sale_refunds'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 14 in versions:
                    for name in ('managed_credit_profiles', 'managed_credit_sales', 'managed_credit_payments'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 15 in versions:
                    for name in ('managed_returns', 'managed_return_lines', 'managed_return_refunds'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 16 in versions:
                    for name in ('managed_return_cancellations', 'managed_return_recaptures'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 17 in versions:
                    for name in ('deposit_packaging_profiles', 'deposit_packaging_components'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 18 in versions:
                    for name in ('managed_deposit_issues', 'managed_deposit_returns', 'managed_deposit_refunds'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                if 19 in versions:
                    required['payment_methods'] = {column.name for column in Base.metadata.tables['payment_methods'].columns}
                if 20 in versions:
                    for name in ('managed_deposit_return_cancellations', 'managed_deposit_return_recaptures'):
                        required[name] = {column.name for column in Base.metadata.tables[name].columns}
                for table_name, required_columns in required.items():
                    if table_name not in tables:
                        raise ValueError(f'Schéma versionné incomplet : table {table_name} absente.')
                    columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table_name}")')}
                    if not required_columns.issubset(columns):
                        raise ValueError(f'Schéma versionné incomplet : colonnes absentes dans {table_name}.')
                if versions == list(range(1, VERSION + 1)):
                    verify_barcode_constraints(db)
                    db.rollback()
                    return None
            # Une seconde connexion lit l'instantané verrouillé, WAL compris.
            try:
                with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as source:
                    with closing(sqlite3.connect(backup)) as target:
                        source.backup(target)
                        _verify(target)
            except Exception:
                backup.unlink(missing_ok=True)
                raise
            if 'depotpro_schema_migrations' not in tables:
                db.execute('CREATE TABLE depotpro_schema_migrations (version INTEGER PRIMARY KEY, description TEXT NOT NULL, applied_at TEXT NOT NULL)')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (1, 'Initialisation de l’historique, sans modification des données métier',
                            datetime.now().isoformat(timespec='seconds')))
            if 2 not in versions:
                # Les relations historiques restent inchangées ; aucun ancien PIN n'est repris.
                if 'owner_security' not in tables:
                    db.execute("CREATE TABLE owner_security (id INTEGER PRIMARY KEY, pin_hash VARCHAR, failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0, inactivity_seconds INTEGER NOT NULL DEFAULT 900, CONSTRAINT owner_security_singleton CHECK (id = 1))")
                else:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(owner_security)')}
                    if not {'id', 'pin_hash', 'failed_attempts', 'locked_until', 'inactivity_seconds'}.issubset(columns):
                        raise ValueError('Table de sécurité incompatible.')
                    if db.execute('SELECT 1 FROM owner_security LIMIT 1').fetchone():
                        raise ValueError('Sécurité propriétaire déjà initialisée sans migration correspondante.')
                db.execute('UPDATE users SET pin_code = NULL WHERE pin_code IS NOT NULL')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (2, 'Sécurité propriétaire et suppression des PIN historiques', datetime.now().isoformat(timespec='seconds')))
            if 3 not in versions:
                if 'product_packagings' not in tables:
                    from sqlalchemy.schema import CreateTable, CreateIndex
                    from sqlalchemy.dialects.sqlite import dialect
                    table = Base.metadata.tables['product_packagings']
                    db.execute(str(CreateTable(table).compile(dialect=dialect())))
                    for index in table.indexes:
                        db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                else:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(product_packagings)')}
                    expected = {col.name for col in Base.metadata.tables['product_packagings'].columns}
                    if columns != expected or db.execute('SELECT 1 FROM product_packagings LIMIT 1').fetchone():
                        raise ValueError('Conditionnements existants non reconnus : aucune migration appliquée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (3, 'Conditionnements par produit, sans conversion ni valeur par défaut', datetime.now().isoformat(timespec='seconds')))
            if 4 not in versions:
                cost_columns = {row[1] for row in db.execute('PRAGMA table_info(products)')}
                cost_fields = {'average_cost_numerator', 'average_cost_denominator'}
                found = cost_fields & cost_columns
                if found and found != cost_fields:
                    raise ValueError('Colonnes de coût moyen partiellement présentes : intervention nécessaire.')
                if not found:
                    db.execute('ALTER TABLE products ADD COLUMN average_cost_numerator VARCHAR')
                    db.execute('ALTER TABLE products ADD COLUMN average_cost_denominator VARCHAR')
                elif db.execute('SELECT 1 FROM products WHERE average_cost_numerator IS NOT NULL OR average_cost_denominator IS NOT NULL LIMIT 1').fetchone():
                    raise ValueError('Coûts moyens non reconnus : aucune migration appliquée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (4, 'Coût moyen exact facultatif, sans estimation initiale', datetime.now().isoformat(timespec='seconds')))
            if 5 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                new_names = ('inventories', 'inventory_lines', 'purchase_receipts', 'purchase_receipt_lines')
                for name in new_names:
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {col.name for col in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                line_cols = {row[1] for row in db.execute('PRAGMA table_info(purchase_order_lines)')}
                new_cols = {'packaging_id': 'INTEGER REFERENCES product_packagings(id)',
                            'packaging_name': 'VARCHAR', 'base_unit': 'VARCHAR',
                            'conversion_factor': 'NUMERIC(10, 3)', 'allow_fraction': 'BOOLEAN'}
                found = set(new_cols) & line_cols
                if found and found != set(new_cols):
                    raise ValueError('Colonnes de conditionnement partiellement présentes.')
                if not found:
                    for name, definition in new_cols.items():
                        db.execute(f'ALTER TABLE purchase_order_lines ADD COLUMN {name} {definition}')
                elif db.execute('SELECT 1 FROM purchase_order_lines WHERE packaging_id IS NOT NULL OR conversion_factor IS NOT NULL LIMIT 1').fetchone():
                    raise ValueError('Conditionnements de commandes non reconnus.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (5, 'Réceptions, inventaires et instantanés de conditionnement', datetime.now().isoformat(timespec='seconds')))
            if 6 not in versions:
                for table_name, columns in (
                    ('purchase_order_lines', {'unit_discount': 'INTEGER', 'unit_fee': 'INTEGER'}),
                    ('supplier_debts', {'receipt_id': 'INTEGER REFERENCES purchase_receipts(id)'}),
                    ('payments', {'cash_link_status': 'VARCHAR'}),
                ):
                    present = {row[1] for row in db.execute(f'PRAGMA table_info("{table_name}")')}
                    found = set(columns) & present
                    if found and found != set(columns):
                        raise ValueError(f'Colonnes partiellement présentes dans {table_name}.')
                    if not found:
                        for name, definition in columns.items():
                            db.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{name}" {definition}')
                    else:
                        condition = ' OR '.join(f'"{name}" IS NOT NULL' for name in columns)
                        if db.execute(f'SELECT 1 FROM "{table_name}" WHERE {condition} LIMIT 1').fetchone():
                            raise ValueError(f'Données non reconnues dans {table_name}.')
                db.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_supplier_debt_receipt ON supplier_debts(receipt_id)')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (6, 'Remises et frais unitaires, lien dette-réception', datetime.now().isoformat(timespec='seconds')))
            if 7 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                table = Base.metadata.tables['returnable_packaging_types']
                if table.name not in tables:
                    db.execute(str(CreateTable(table).compile(dialect=dialect())))
                    for index in table.indexes:
                        db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                else:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(returnable_packaging_types)')}
                    if columns != {col.name for col in table.columns} or db.execute('SELECT 1 FROM returnable_packaging_types LIMIT 1').fetchone():
                        raise ValueError('Catalogue d’emballages existant non reconnu : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (7, 'Catalogue séparé des emballages physiques, sans stock ni valeur prédéfinie', datetime.now().isoformat(timespec='seconds')))
            if 8 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('returnable_stock_balances', 'returnable_stock_movements'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {col.name for col in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (8, 'Stock de vides séparé et journal de mouvements', datetime.now().isoformat(timespec='seconds')))
            if 9 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_cash_sessions', 'managed_cash_entries'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {col.name for col in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (9, 'Caisse sécurisée pour règlements fournisseurs futurs', datetime.now().isoformat(timespec='seconds')))
            if 10 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_sales', 'managed_sale_lines', 'managed_cash_transactions'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {col.name for col in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (10, 'Ventes au comptant et mouvements de caisse complémentaires', datetime.now().isoformat(timespec='seconds')))
            if 11 not in versions:
                if db.execute('SELECT 1 FROM products p JOIN product_packagings c ON p.barcode = c.barcode LIMIT 1').fetchone():
                    raise ValueError('Codes-barres identiques entre produits et conditionnements : migration annulée, diagnostic requis.')
                for name, sql in TRIGGERS.items():
                    if db.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?", (name,)).fetchone():
                        raise ValueError(f'Protection de code-barres préexistante non reconnue : {name}.')
                    db.execute(sql)
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (11, 'Unicité inter-tables des codes-barres', datetime.now().isoformat(timespec='seconds')))
            if 12 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                table = Base.metadata.tables['managed_sale_payments']
                if table.name not in tables:
                    db.execute(str(CreateTable(table).compile(dialect=dialect())))
                    for index in table.indexes:
                        db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                else:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(managed_sale_payments)')}
                    if columns != {column.name for column in table.columns} or db.execute('SELECT 1 FROM managed_sale_payments LIMIT 1').fetchone():
                        raise ValueError('Paiements de ventes non reconnus : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (12, 'Paiements multiples des nouvelles ventes', datetime.now().isoformat(timespec='seconds')))
            if 13 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_sale_cancellations', 'managed_sale_refunds'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (13, 'Annulations totales de ventes et remboursements liés', datetime.now().isoformat(timespec='seconds')))
            if 14 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_credit_profiles', 'managed_credit_sales', 'managed_credit_payments'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (14, 'Créances et règlements du nouveau circuit', datetime.now().isoformat(timespec='seconds')))
            if 15 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_returns', 'managed_return_lines', 'managed_return_refunds'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (15, 'Retours partiels et remboursements liés', datetime.now().isoformat(timespec='seconds')))
            if 16 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_return_cancellations', 'managed_return_recaptures'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (16, 'Annulation de retours et reprises de remboursements', datetime.now().isoformat(timespec='seconds')))
            if 17 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('deposit_packaging_profiles', 'deposit_packaging_components'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (17, 'Configuration explicite des emballages par conditionnement', datetime.now().isoformat(timespec='seconds')))
            if 18 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_deposit_issues', 'managed_deposit_returns', 'managed_deposit_refunds'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (18, 'Ventes consignées et retours de vides', datetime.now().isoformat(timespec='seconds')))
            if 19 not in versions:
                from sqlalchemy.schema import CreateTable
                from sqlalchemy.dialects.sqlite import dialect
                from services.cash_methods import METHODS
                table = Base.metadata.tables['payment_methods']
                if 'payment_methods' not in tables:
                    db.execute(str(CreateTable(table).compile(dialect=dialect())))
                else:
                    columns = {row[1] for row in db.execute('PRAGMA table_info(payment_methods)')}
                    if columns != {column.name for column in table.columns} or db.execute('SELECT 1 FROM payment_methods LIMIT 1').fetchone():
                        raise ValueError('Table payment_methods non reconnue : migration annulée.')
                db.executemany('INSERT INTO payment_methods (code, label, active) VALUES (?, ?, 1)', list(METHODS.items()))
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (19, 'Catalogue des moyens de paiement', datetime.now().isoformat(timespec='seconds')))
            if 20 not in versions:
                from sqlalchemy.schema import CreateTable, CreateIndex
                from sqlalchemy.dialects.sqlite import dialect
                for name in ('managed_deposit_return_cancellations', 'managed_deposit_return_recaptures'):
                    table = Base.metadata.tables[name]
                    if name not in tables:
                        db.execute(str(CreateTable(table).compile(dialect=dialect())))
                        for index in table.indexes:
                            db.execute(str(CreateIndex(index).compile(dialect=dialect())))
                    else:
                        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{name}")')}
                        if columns != {column.name for column in table.columns} or db.execute(f'SELECT 1 FROM "{name}" LIMIT 1').fetchone():
                            raise ValueError(f'Table {name} non reconnue : migration annulée.')
                db.execute('INSERT INTO depotpro_schema_migrations VALUES (?, ?, ?)',
                           (20, 'Contrepassation des retours de vides', datetime.now().isoformat(timespec='seconds')))
            verify_barcode_constraints(db)
            _verify(db)
            db.commit()
            return backup
        except Exception:
            db.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application-arretee', action='store_true',
                        help='Confirmer l’arrêt de DEPOTPRO et de tous les accès à la base')
    args = parser.parse_args()
    if not args.application_arretee:
        parser.error('Arrêtez DEPOTPRO puis confirmez avec --application-arretee.')
    try:
        backup = migrate(DB_PATH)
    except (sqlite3.Error, ValueError, OSError) as exc:
        parser.exit(1, f'Migration impossible : {exc}\n')
    print(f'Migrations 1–{VERSION} appliquées. Sauvegarde préalable : {backup}' if backup else f'Migrations 1–{VERSION} déjà appliquées ; aucune modification.')


if __name__ == '__main__':
    main()
