import sqlite3

import pytest

from scripts.migrate_database import migrate


def make_db(path):
    from database import Base
    from sqlalchemy import create_engine
    import models  # noqa: F401
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE owner_security')
        db.execute('DROP TABLE product_packagings')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('INSERT INTO categories (id, name, is_active) VALUES (1, "Boissons", 1)')
        db.execute("INSERT INTO products (id, name, reference, category_id) VALUES (1, 'historique', 'P1', 1)")


def test_migration_avec_sauvegarde_et_reexecution(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    backup = migrate(path)
    assert backup.is_file()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT version FROM depotpro_schema_migrations').fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,)]
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='depotpro_schema_migrations'").fetchone()[0] == 0
    assert migrate(path) is None


def test_refuse_base_etrangere_sans_modification(tmp_path):
    path = tmp_path / 'autre.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE autre (id INTEGER)')
    with pytest.raises(ValueError, match='DEPOTPRO'):
        migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='depotpro_schema_migrations'").fetchone()[0] == 0
    assert list(tmp_path.glob('*avant_migration*')) == []


def test_refuse_historique_inconnu(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE depotpro_schema_migrations (version INTEGER PRIMARY KEY, description TEXT, applied_at TEXT)')
        db.execute("INSERT INTO depotpro_schema_migrations VALUES (99, 'futur', 'date')")
    with pytest.raises(ValueError, match='non reconnu'):
        migrate(path)
    assert list(tmp_path.glob('*avant_migration*')) == []


def test_migration_annulee_si_validation_finale_echoue(tmp_path, monkeypatch):
    import scripts.migrate_database as migrations
    path = tmp_path / 'depot.db'
    make_db(path)
    original = migrations._verify
    calls = 0

    def fail_final_check(connection):
        nonlocal calls
        calls += 1
        original(connection)
        if calls == 3:
            raise ValueError('Échec simulé')

    monkeypatch.setattr(migrations, '_verify', fail_final_check)
    with pytest.raises(ValueError, match='simulé'):
        migrations.migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='depotpro_schema_migrations'").fetchone()[0] == 0
    backups = list(tmp_path.glob('*avant_migration*'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)


def test_migration_refuse_cles_etrangeres_invalides(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE invalid (id INTEGER REFERENCES products(id))')
        db.execute('INSERT INTO invalid VALUES (999)')
    with pytest.raises(ValueError, match='étrangères'):
        migrate(path)
    assert list(tmp_path.glob('*avant_migration*')) == []


def test_migration_sauvegarde_un_wal_non_vide(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    writer = sqlite3.connect(path)
    writer.execute('PRAGMA wal_autocheckpoint=0')
    writer.execute("INSERT INTO products (id, name, reference, category_id) VALUES (2, 'transaction WAL', 'P2', 1)")
    writer.commit()
    try:
        backup = migrate(path)
        with sqlite3.connect(backup) as db:
            assert db.execute('SELECT name FROM products WHERE id=2').fetchone() == ('transaction WAL',)
    finally:
        writer.close()


def test_migration_ancien_pin_et_retour_arriere(tmp_path):
    from scripts.restore_backup import restore
    path = tmp_path / 'depot.db'
    make_db(path)
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO users (id, username, pin_code) VALUES (1, 'historique', '0000')")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT username, pin_code FROM users').fetchone() == ('historique', None)
        assert db.execute('SELECT count(*) FROM owner_security').fetchone()[0] == 0
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT pin_code FROM users').fetchone()[0] == '0000'
    with pytest.raises(ValueError, match='schéma'):
        restore(backup, path)
    safety = restore(backup, path, allow_schema_change=True)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT pin_code FROM users').fetchone()[0] == '0000'
    with sqlite3.connect(safety) as db:
        assert db.execute('SELECT pin_code FROM users').fetchone()[0] is None


def test_migration_depuis_version_1_sauvegarde_les_donnees(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE depotpro_schema_migrations (version INTEGER PRIMARY KEY, description TEXT NOT NULL, applied_at TEXT NOT NULL)')
        db.execute("INSERT INTO depotpro_schema_migrations VALUES (1, 'initial', 'date')")
        db.execute("INSERT INTO users (id, username, pin_code) VALUES (1, 'proprietaire', '1234')")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,)]
        assert db.execute('SELECT username, pin_code FROM users').fetchone() == ('proprietaire', None)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT username, pin_code FROM users').fetchone() == ('proprietaire', '1234')


def test_migration_v3_preserve_pin_et_historique(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE product_packagings')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (3,4,5,6,7,8,9,10)')
        db.execute("INSERT INTO owner_security (id, pin_hash, failed_attempts, locked_until, inactivity_seconds) VALUES (1, 'hash-existant', 0, 0, 900)")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-existant',)
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT COUNT(*) FROM product_packagings').fetchone() == (0,)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-existant',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='product_packagings'").fetchone() == (0,)


def test_migration_v4_preserve_packagings_et_cout_inconnu(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (4,5,6,7,8,9,10)')
        db.execute('ALTER TABLE products DROP COLUMN average_cost_numerator')
        db.execute('ALTER TABLE products DROP COLUMN average_cost_denominator')
        db.execute("INSERT INTO product_packagings (product_id, name, base_unit, coefficient, allow_fraction, is_active) VALUES (1, 'pack', 'bouteille', 6, 0, 1)")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT average_cost_numerator, average_cost_denominator FROM products').fetchone() == (None, None)
        assert db.execute('SELECT coefficient FROM product_packagings').fetchone() == (6,)
    with sqlite3.connect(backup) as db:
        assert 'average_cost_numerator' not in {col[1] for col in db.execute('PRAGMA table_info(products)')}


def test_refuse_schema_versionne_incomplet_sans_migration(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (4,5,6,7,8,9,10)')
        db.execute('DROP TABLE product_packagings')
    with pytest.raises(ValueError, match='incomplet'):
        migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(1,), (2,), (3,)]


def test_migration_v5_depuis_v4_sauvegarde_et_conservation(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        for name in ('purchase_receipt_lines', 'purchase_receipts', 'inventory_lines', 'inventories'):
            db.execute(f'DROP TABLE {name}')
        db.execute('DROP TABLE purchase_order_lines')
        db.execute('CREATE TABLE purchase_order_lines (id INTEGER PRIMARY KEY, purchase_order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, ordered_quantity NUMERIC NOT NULL, received_quantity NUMERIC, unit_price INTEGER NOT NULL, line_total INTEGER NOT NULL)')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (5,6,7,8,9,10)')
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,)]
        assert 'conversion_factor' in {col[1] for col in db.execute('PRAGMA table_info(purchase_order_lines)')}
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='purchase_receipts'").fetchone() == (1,)
    with sqlite3.connect(backup) as db:
        assert 'conversion_factor' not in {col[1] for col in db.execute('PRAGMA table_info(purchase_order_lines)')}
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)


def test_migration_v6_depuis_v5_preserve_dette_historique(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('ALTER TABLE payments DROP COLUMN cash_link_status')
        db.execute('ALTER TABLE purchase_order_lines DROP COLUMN unit_discount')
        db.execute('ALTER TABLE purchase_order_lines DROP COLUMN unit_fee')
        # Reconstituer la table v5 sans le lien à une réception.
        db.execute('DROP TABLE supplier_debts')
        db.execute('CREATE TABLE supplier_debts (id INTEGER PRIMARY KEY, reference VARCHAR NOT NULL, supplier_id INTEGER NOT NULL, purchase_order_id INTEGER, date DATETIME, initial_amount INTEGER NOT NULL, paid_amount INTEGER, remaining_amount INTEGER NOT NULL, due_date DATETIME, status VARCHAR, is_cancelled BOOLEAN)')
        db.execute("INSERT INTO suppliers (id, code, name, phone) VALUES (1, 'F', 'Ancien fournisseur', '01')")
        db.execute("INSERT INTO supplier_debts (reference, supplier_id, initial_amount, remaining_amount) VALUES ('D1', 1, 1000, 1000)")
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (6,7,8,9,10)')
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT initial_amount, remaining_amount, receipt_id FROM supplier_debts').fetchone() == (1000, 1000, None)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,)]
    with sqlite3.connect(backup) as db:
        assert 'receipt_id' not in {col[1] for col in db.execute('PRAGMA table_info(supplier_debts)')}
        assert db.execute('SELECT initial_amount, remaining_amount FROM supplier_debts').fetchone() == (1000, 1000)


def test_migration_v7_depuis_v6_preserve_donnees_et_sauvegarde(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE returnable_packaging_types')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (7,8,9,10)')
        db.execute("INSERT INTO owner_security (id, pin_hash, failed_attempts, locked_until, inactivity_seconds) VALUES (1, 'hash-preexistant', 0, 0, 900)")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-preexistant',)
        assert db.execute('SELECT count(*) FROM returnable_packaging_types').fetchone() == (0,)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, 11)]
    with sqlite3.connect(backup) as db:
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='returnable_packaging_types'").fetchone() == (0,)
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-preexistant',)
    assert migrate(path) is None


def test_migration_v7_refuse_catalogue_non_versionne(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (7,8,9,10)')
        db.execute("INSERT INTO returnable_packaging_types (code, name, producer, kind, is_active, created_at) VALUES ('X', 'existant', 'test', 'crate', 1, '2026-01-01')")
    with pytest.raises(ValueError, match='non reconnu'):
        migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM returnable_packaging_types').fetchone() == ('existant',)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (6,)


def test_migration_v8_stock_vides_vide_et_catalogue_conserve(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE returnable_stock_movements')
        db.execute('DROP TABLE returnable_stock_balances')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (8,9,10)')
        db.execute("INSERT INTO returnable_packaging_types (code, name, producer, kind, is_active, created_at) VALUES ('CAS', 'Casier test', 'Test', 'crate', 1, '2026-01-01')")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT code FROM returnable_packaging_types').fetchone() == ('CAS',)
        assert db.execute('SELECT count(*) FROM returnable_stock_balances').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM returnable_stock_movements').fetchone() == (0,)
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT code FROM returnable_packaging_types').fetchone() == ('CAS',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='returnable_stock_balances'").fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v8_refuse_stock_non_versionne(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (8,9,10)')
        db.execute("INSERT INTO returnable_packaging_types (id, code, name, producer, kind, is_active, created_at) VALUES (1, 'CAS', 'Test', 'Test', 'crate', 1, '2026-01-01')")
        db.execute('INSERT INTO returnable_stock_balances VALUES (1, 10)')
    with pytest.raises(ValueError, match='non reconnue'):
        migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT quantity FROM returnable_stock_balances').fetchone() == (10,)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (7,)


def test_migration_v9_preserve_paiements_hors_caisse(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE managed_cash_entries')
        db.execute('DROP TABLE managed_cash_sessions')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (9,10)')
        db.execute("INSERT INTO payments (reference, amount, payment_method, cash_link_status) VALUES ('P-HIST', 1000, 'cash', 'outside_cash')")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT reference, amount, cash_link_status FROM payments').fetchone() == ('P-HIST', 1000, 'outside_cash')
        assert db.execute('SELECT count(*) FROM managed_cash_sessions').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM managed_cash_entries').fetchone() == (0,)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT amount, cash_link_status FROM payments').fetchone() == (1000, 'outside_cash')
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_cash_sessions'").fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v10_preserve_mouvements_caisse_v9(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        for table in ('managed_cash_transactions', 'managed_sale_lines', 'managed_sales'):
            db.execute(f'DROP TABLE {table}')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version=10')
        db.execute("INSERT INTO managed_cash_sessions (reference, opening_key, opened_at, status, opening_cash) VALUES ('CAISSE-H', 'ancien', '2026-01-01', 'closed', 500)")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT reference, opening_cash FROM managed_cash_sessions').fetchone() == ('CAISSE-H', 500)
        assert db.execute('SELECT count(*) FROM managed_sales').fetchone() == (0,)
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT reference FROM managed_cash_sessions').fetchone() == ('CAISSE-H',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_sales'").fetchone() == (0,)
    assert migrate(path) is None
