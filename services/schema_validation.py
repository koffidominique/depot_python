"""Contrôles de schéma SQLite, en lecture seule, avant ouverture de l'interface.

Ils couvrent les invariants critiques connus, pas l'ensemble des contraintes SQL
ni la cohérence comptable des historiques.
"""
import re
from database import Base
from services.barcode_constraints import verify_barcode_constraints

# Une seule colonne par index dans cette liste ; les index partiels ne sont pas
# équivalents à une contrainte d'unicité globale.
REQUIRED_UNIQUE = {
    'products': ('barcode',),
    'product_packagings': ('barcode',),
    'purchase_receipts': ('request_key',),
    'supplier_debts': ('receipt_id',),
    'managed_sales': ('request_key',),
    'managed_cash_sessions': ('opening_key', 'closing_key'),
    'managed_cash_entries': ('supplier_payment_id',),
    'managed_cash_transactions': ('request_key', 'sale_id'),
    'managed_sale_payments': ('transaction_id',),
    'managed_sale_cancellations': ('sale_id', 'request_key'),
    'managed_sale_refunds': ('original_transaction_id', 'refund_transaction_id'),
    'managed_credit_sales': ('sale_id',),
    'managed_credit_payments': ('transaction_id', 'request_key'),
    'managed_returns': ('request_key',),
    'managed_return_refunds': ('refund_transaction_id',),
    'managed_return_cancellations': ('return_id', 'request_key'),
    'managed_return_recaptures': ('refund_id', 'transaction_id'),
    'managed_deposit_returns': ('request_key', 'stock_movement_id'),
    'managed_deposit_refunds': ('refund_transaction_id',),
    'managed_deposit_return_cancellations': ('return_id', 'stock_movement_id', 'request_key'),
    'managed_deposit_return_recaptures': ('refund_id', 'transaction_id'),
    'returnable_stock_movements': ('request_key',),
}


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def validate_schema(db):
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Échec du contrôle d’intégrité SQLite.')
    if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
        raise ValueError('Clés étrangères incohérentes.')
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            raise ValueError(f'Table manquante : {table.name}.')
        columns = {row[1] for row in db.execute(f'PRAGMA table_info({_quote(table.name)})')}
        missing = {column.name for column in table.columns} - columns
        if missing:
            raise ValueError(f'Colonnes manquantes dans {table.name} : {", ".join(sorted(missing))}.')
    for table_name, required in REQUIRED_UNIQUE.items():
        found = set()
        for idx in db.execute(f'PRAGMA index_list({_quote(table_name)})').fetchall():
            if not idx[2] or idx[4]:
                continue
            columns = [row[2] for row in db.execute(f'PRAGMA index_info({_quote(idx[1])})')]
            if len(columns) == 1:
                found.add(columns[0])
        if not set(required).issubset(found):
            raise ValueError(f'Index unique requis absent dans {table_name}.')
    method_info = db.execute('PRAGMA table_info(payment_methods)').fetchall()
    if not any(row[1] == 'code' and row[5] == 1 for row in method_info):
        raise ValueError('Clé du catalogue des moyens de paiement absente.')
    cash = db.execute("SELECT active FROM payment_methods WHERE code='cash'").fetchone()
    if not cash or cash[0] != 1:
        raise ValueError('Moyen espèces actif absent.')
    indexes = db.execute('PRAGMA index_list(deposit_packaging_components)').fetchall()
    unique_component = False
    for idx in indexes:
        if idx[2] and not idx[4]:
            columns = [row[2] for row in db.execute(f'PRAGMA index_info({_quote(idx[1])})')]
            if columns == ['packaging_id', 'returnable_id']:
                unique_component = True
                break
    if not unique_component:
        raise ValueError('Unicité de composition des emballages absente.')
    profile_info = db.execute('PRAGMA table_info(deposit_packaging_profiles)').fetchall()
    if not any(row[1] == 'packaging_id' and row[5] == 1 for row in profile_info):
        raise ValueError('Clé de configuration des consignes absente.')
    indexes = db.execute('PRAGMA index_list(managed_cash_sessions)').fetchall()
    partial = next((idx for idx in indexes if idx[1] == 'uq_managed_cash_open' and idx[2] and idx[4]), None)
    if not partial:
        raise ValueError('Index de session de caisse unique absent.')
    columns = [row[2] for row in db.execute(f'PRAGMA index_info({_quote(partial[1])})')]
    definition = db.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name=?", (partial[1],)).fetchone()
    if columns != ['status'] or not definition or not definition[0] or not re.search(r"\bWHERE\s+status\s*=\s*'open'\s*$", definition[0], re.I):
        raise ValueError('Index de session de caisse unique incompatible.')

    verify_barcode_constraints(db)
