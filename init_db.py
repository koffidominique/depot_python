"""Initialisation sans identifiant par défaut ni migration silencieuse."""
import sqlite3
from contextlib import closing
from config import DB_PATH
from database import Base, engine
import models  # noqa: F401
from scripts.migrate_database import migrate


def initialize_database():
    existed = DB_PATH.exists()
    if not existed:
        Base.metadata.create_all(bind=engine)
        engine.dispose()
        migrate(DB_PATH)
        return
    with closing(sqlite3.connect(DB_PATH.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'depotpro_schema_migrations' not in tables:
            raise RuntimeError('Base existante non migrée. Arrêtez l’application, sauvegardez-la et exécutez python scripts/migrate_database.py --application-arretee.')
        versions = [row[0] for row in db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version')]
        product_columns = {row[1] for row in db.execute('PRAGMA table_info(products)')}
        purchase_columns = {row[1] for row in db.execute('PRAGMA table_info(purchase_order_lines)')}
        debt_columns = {row[1] for row in db.execute('PRAGMA table_info(supplier_debts)')}
        payment_columns = {row[1] for row in db.execute('PRAGMA table_info(payments)')}
        stock_balance_columns = {row[1] for row in db.execute('PRAGMA table_info(returnable_stock_balances)')}
        stock_movement_columns = {row[1] for row in db.execute('PRAGMA table_info(returnable_stock_movements)')}
        managed_session_columns = {row[1] for row in db.execute('PRAGMA table_info(managed_cash_sessions)')}
        managed_entry_columns = {row[1] for row in db.execute('PRAGMA table_info(managed_cash_entries)')}
        managed_sale_columns = {row[1] for row in db.execute('PRAGMA table_info(managed_sales)')}
        managed_line_columns = {row[1] for row in db.execute('PRAGMA table_info(managed_sale_lines)')}
        managed_transaction_columns = {row[1] for row in db.execute('PRAGMA table_info(managed_cash_transactions)')}
        returnable_columns = {row[1] for row in db.execute('PRAGMA table_info(returnable_packaging_types)')}
        if (versions != [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] or not {'owner_security', 'product_packagings', 'inventories', 'inventory_lines', 'purchase_receipts', 'purchase_receipt_lines', 'returnable_packaging_types', 'returnable_stock_balances', 'returnable_stock_movements', 'managed_cash_sessions', 'managed_cash_entries', 'managed_sales', 'managed_sale_lines', 'managed_cash_transactions'}.issubset(tables)
                or not {'average_cost_numerator', 'average_cost_denominator'}.issubset(product_columns)
                or not {'unit_discount', 'unit_fee'}.issubset(purchase_columns) or 'receipt_id' not in debt_columns or 'cash_link_status' not in payment_columns
                or not {'id', 'code', 'name', 'producer', 'kind', 'description', 'deposit_value', 'is_active', 'created_at'}.issubset(returnable_columns)
                or not {'packaging_id', 'quantity'}.issubset(stock_balance_columns)
                or not {'id', 'request_key', 'packaging_id', 'date', 'movement_type', 'quantity', 'stock_before', 'stock_after', 'reason', 'reference_document'}.issubset(stock_movement_columns)
                or not {'id', 'reference', 'opening_key', 'closing_key', 'opened_at', 'closed_at', 'status', 'opening_cash', 'theoretical_cash', 'physical_cash', 'difference', 'closing_notes'}.issubset(managed_session_columns)
                or not {'id', 'session_id', 'supplier_payment_id', 'date', 'method', 'amount'}.issubset(managed_entry_columns)
                or not {'id', 'reference', 'request_key', 'request_fingerprint', 'created_at', 'mode', 'total', 'payment_method'}.issubset(managed_sale_columns)
                or not {'id', 'sale_id', 'product_id', 'packaging_id', 'packaging_name', 'base_unit', 'coefficient', 'quantity', 'base_quantity', 'unit_price', 'amount', 'cost_numerator', 'cost_denominator'}.issubset(managed_line_columns)
                or not {'id', 'session_id', 'request_key', 'sale_id', 'date', 'kind', 'method', 'amount', 'description', 'category', 'beneficiary', 'reference'}.issubset(managed_transaction_columns)):
            raise RuntimeError('Base nécessitant une migration. Arrêtez l’application puis exécutez python scripts/migrate_database.py --application-arretee.')


if __name__ == '__main__':
    initialize_database()
