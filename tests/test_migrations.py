import sqlite3

import pytest

from scripts.migrate_database import migrate, VERSION
from services.barcode_constraints import TRIGGERS


def drop_barcode_triggers(db):
    for name in TRIGGERS:
        db.execute(f'DROP TRIGGER IF EXISTS {name}')


def make_db(path):
    from database import Base
    from sqlalchemy import create_engine
    import models  # noqa: F401
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE payment_methods')
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
        assert db.execute('SELECT version FROM depotpro_schema_migrations').fetchall() == [(i,) for i in range(1, VERSION + 1)]
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        from services.schema_validation import validate_schema
        validate_schema(db)
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
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, VERSION + 1)]
        assert db.execute('SELECT username, pin_code FROM users').fetchone() == ('proprietaire', None)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT username, pin_code FROM users').fetchone() == ('proprietaire', '1234')


def test_migration_v3_preserve_pin_et_historique(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE product_packagings')
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, VERSION + 1)]
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT initial_amount, remaining_amount, receipt_id FROM supplier_debts').fetchone() == (1000, 1000, None)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, VERSION + 1)]
    with sqlite3.connect(backup) as db:
        assert 'receipt_id' not in {col[1] for col in db.execute('PRAGMA table_info(supplier_debts)')}
        assert db.execute('SELECT initial_amount, remaining_amount FROM supplier_debts').fetchone() == (1000, 1000)


def test_migration_v7_depuis_v6_preserve_donnees_et_sauvegarde(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE returnable_packaging_types')
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
        db.execute("INSERT INTO owner_security (id, pin_hash, failed_attempts, locked_until, inactivity_seconds) VALUES (1, 'hash-preexistant', 0, 0, 900)")
    backup = migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM products').fetchone() == ('historique',)
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-preexistant',)
        assert db.execute('SELECT count(*) FROM returnable_packaging_types').fetchone() == (0,)
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, VERSION + 1)]
    with sqlite3.connect(backup) as db:
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='returnable_packaging_types'").fetchone() == (0,)
        assert db.execute('SELECT pin_hash FROM owner_security').fetchone() == ('hash-preexistant',)
    assert migrate(path) is None


def test_migration_v7_refuse_catalogue_non_versionne(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (7,8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (8,9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (9,10,11,12,13,14,15,16,17,18,19,20)')
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
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (10,11,12,13,14,15,16,17,18,19,20)')
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


def test_migration_v11_controle_codes_barres_direct_sql(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (11,12,13,14,15,16,17,18,19,20)')
        db.execute("UPDATE products SET barcode='PRODUIT' WHERE id=1")
        db.execute("INSERT INTO product_packagings (product_id,name,base_unit,coefficient,barcode,allow_fraction,is_active) VALUES (1,'pack','bouteille',6,'PACK',0,1)")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT barcode FROM products WHERE id=1').fetchone() == ('PRODUIT',)
        assert db.execute('SELECT barcode FROM product_packagings').fetchone() == ('PACK',)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (10,)
    with sqlite3.connect(path) as db:
        for sql in (
            "INSERT INTO products (name,reference,category_id,barcode) VALUES ('Test','TEST',1,'PACK')",
            "UPDATE products SET barcode='PACK' WHERE id=1",
            "INSERT INTO product_packagings (product_id,name,base_unit,coefficient,barcode,allow_fraction,is_active) VALUES (1,'casier','bouteille',24,'PRODUIT',0,1)",
            "UPDATE product_packagings SET barcode='PRODUIT' WHERE product_id=1",
        ):
            with pytest.raises(sqlite3.IntegrityError, match='Code-barres'):
                db.execute(sql)
        assert db.execute('SELECT barcode FROM products WHERE id=1').fetchone() == ('PRODUIT',)
        assert db.execute('SELECT barcode FROM product_packagings').fetchone() == ('PACK',)
    assert migrate(path) is None


def test_migration_v11_refuse_collision_sans_modifier_donnees(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        drop_barcode_triggers(db)
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (11,12,13,14,15,16,17,18,19,20)')
        db.execute("UPDATE products SET barcode='CONFLIT' WHERE id=1")
        db.execute("INSERT INTO product_packagings (product_id,name,base_unit,coefficient,barcode,allow_fraction,is_active) VALUES (1,'pack','bouteille',6,'CONFLIT',0,1)")
    with pytest.raises(ValueError, match='Codes-barres identiques'):
        migrate(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT barcode FROM products').fetchone() == ('CONFLIT',)
        assert db.execute('SELECT barcode FROM product_packagings').fetchone() == ('CONFLIT',)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (10,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'barcode_%'").fetchone() == (0,)
    backups = list(tmp_path.glob('*avant_migration*.db'))
    assert backups
    with sqlite3.connect(max(backups, key=lambda p: p.stat().st_mtime_ns)) as db:
        assert db.execute('SELECT barcode FROM products').fetchone() == ('CONFLIT',)


def test_migration_v12_garde_vente_et_caisse_historiques_sans_reconstruction(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE managed_sale_payments')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (12,13,14,15,16,17,18,19,20)')
        db.execute("INSERT INTO managed_cash_sessions (id,reference,opening_key,opened_at,status,opening_cash) VALUES (1,'CS','open','2026-01-01','open',1000)")
        db.execute("INSERT INTO managed_sales (id,reference,request_key,request_fingerprint,created_at,mode,total,payment_method) VALUES (1,'S','sale','history','2026-01-01','retail',3000,'cash')")
        db.execute("INSERT INTO managed_cash_transactions (session_id,request_key,sale_id,date,kind,method,amount,description) VALUES (1,'old',1,'2026-01-01','sale','cash',3000,'Vente')")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT total FROM managed_sales').fetchone() == (3000,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_sale_payments'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT total FROM managed_sales').fetchone() == (3000,)
        assert db.execute('SELECT amount FROM managed_cash_transactions').fetchone() == (3000,)
        assert db.execute('SELECT count(*) FROM managed_sale_payments').fetchone() == (0,)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (VERSION,)
    assert migrate(path) is None


def test_migration_v13_conserve_vente_et_mouvement_existants(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE managed_sale_refunds')
        db.execute('DROP TABLE managed_sale_cancellations')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (13,14,15,16,17,18,19,20)')
        db.execute("INSERT INTO managed_cash_sessions (id,reference,opening_key,opened_at,status,opening_cash) VALUES (1,'CS','open','2026-01-01','open',1000)")
        db.execute("INSERT INTO managed_sales (id,reference,request_key,request_fingerprint,created_at,mode,total,payment_method) VALUES (1,'S','sale','history','2026-01-01','retail',3000,'cash')")
        db.execute("INSERT INTO managed_cash_transactions (session_id,request_key,sale_id,date,kind,method,amount,description) VALUES (1,'old',1,'2026-01-01','sale','cash',3000,'Vente')")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT amount FROM managed_cash_transactions').fetchone() == (3000,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_sale_cancellations'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT total FROM managed_sales').fetchone() == (3000,)
        assert db.execute('SELECT amount FROM managed_cash_transactions').fetchone() == (3000,)
        assert db.execute('SELECT count(*) FROM managed_sale_cancellations').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM managed_sale_refunds').fetchone() == (0,)
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (VERSION,)
    assert migrate(path) is None


def test_migration_v14_preserve_creance_historique_sans_rapprochement(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        for table in ('managed_credit_payments', 'managed_credit_sales', 'managed_credit_profiles'):
            db.execute(f'DROP TABLE {table}')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (14,15,16,17,18,19,20)')
        db.execute("INSERT INTO clients (id,code,name,type,credit_limit,financial_balance,consignment_balance,payment_terms,is_active,created_at) VALUES (1,'OLD','Ancien','particulier',0,500,0,0,1,'2026-01-01')")
        db.execute("INSERT INTO client_debts (reference,client_id,date,initial_amount,paid_amount,remaining_amount) VALUES ('DETTE',1,'2026-01-01',500,0,500)")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT remaining_amount FROM client_debts').fetchone() == (500,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_credit_sales'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT remaining_amount FROM client_debts').fetchone() == (500,)
        assert db.execute('SELECT financial_balance FROM clients').fetchone() == (500,)
        assert db.execute('SELECT count(*) FROM managed_credit_profiles').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM managed_credit_sales').fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v15_conserve_credit_et_vente_sans_creer_retour(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        for table in ('managed_return_refunds', 'managed_return_lines', 'managed_returns'):
            db.execute(f'DROP TABLE {table}')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (15,16,17,18,19,20)')
        db.execute("INSERT INTO clients (id,code,name,type,credit_limit,financial_balance,consignment_balance,payment_terms,is_active,created_at) VALUES (1,'C','Client','professionnel',0,0,0,0,1,'2026-01-01')")
        db.execute("INSERT INTO managed_sales (id,reference,request_key,request_fingerprint,created_at,mode,total,payment_method) VALUES (1,'V','vente','fingerprint','2026-01-01','retail',3000,'credit')")
        db.execute("INSERT INTO managed_credit_sales (sale_id,client_id,initial_amount,remaining_amount,created_at) VALUES (1,1,3000,3000,'2026-01-01')")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT remaining_amount FROM managed_credit_sales').fetchone() == (3000,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_returns'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT remaining_amount FROM managed_credit_sales').fetchone() == (3000,)
        assert db.execute('SELECT total FROM managed_sales').fetchone() == (3000,)
        assert db.execute('SELECT count(*) FROM managed_returns').fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v16_preserve_retour_existant_sans_annulation(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE managed_return_recaptures')
        db.execute('DROP TABLE managed_return_cancellations')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (16,17,18,19,20)')
        db.execute("INSERT INTO managed_cash_sessions (id,reference,opening_key,opened_at,status,opening_cash) VALUES (1,'C','K','2026-01-01','open',500)")
        db.execute("INSERT INTO managed_sales (id,reference,request_key,request_fingerprint,created_at,mode,total,payment_method) VALUES (1,'V','S','FP','2026-01-01','retail',1000,'cash')")
        db.execute("INSERT INTO managed_returns (sale_id,session_id,request_key,fingerprint,reason,total,credit_reduction,created_at) VALUES (1,1,'RET','FP','Retour',500,0,'2026-01-01')")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT total FROM managed_returns').fetchone() == (500,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_return_cancellations'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT total FROM managed_returns').fetchone() == (500,)
        assert db.execute('SELECT count(*) FROM managed_return_cancellations').fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v17_ne_suppose_aucune_consigne(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE deposit_packaging_components')
        db.execute('DROP TABLE deposit_packaging_profiles')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (17,18,19,20)')
        db.execute("INSERT INTO product_packagings (product_id,name,base_unit,coefficient,allow_fraction,is_active) VALUES (1,'casier','bouteille',24,0,1)")
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT coefficient FROM product_packagings').fetchone() == (24,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='deposit_packaging_profiles'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT coefficient FROM product_packagings').fetchone() == (24,)
        assert db.execute('SELECT count(*) FROM deposit_packaging_profiles').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM deposit_packaging_components').fetchone() == (0,)
    assert migrate(path) is None


def test_migration_v18_preserve_configuration_sans_creer_consigne(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        for table in ('managed_deposit_refunds', 'managed_deposit_returns', 'managed_deposit_issues'):
            db.execute(f'DROP TABLE {table}')
        db.execute('DELETE FROM payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (18,19,20)')
        db.execute("INSERT INTO product_packagings (id,product_id,name,base_unit,coefficient,allow_fraction,is_active) VALUES (1,1,'casier','bouteille',24,0,1)")
        db.execute("INSERT INTO returnable_packaging_types (id,code,name,producer,kind,deposit_value,is_active,created_at) VALUES (1,'CAS','Casier','Test','crate',500,1,'2026-01-01')")
        db.execute("INSERT INTO deposit_packaging_profiles (packaging_id,mode) VALUES (1,'deposit')")
        db.execute('INSERT INTO deposit_packaging_components (packaging_id,returnable_id,pieces_per_pack) VALUES (1,1,1)')
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT pieces_per_pack FROM deposit_packaging_components').fetchone() == (1,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='managed_deposit_issues'").fetchone() == (0,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT pieces_per_pack FROM deposit_packaging_components').fetchone() == (1,)
        assert db.execute('SELECT count(*) FROM managed_deposit_issues').fetchone() == (0,)
        assert db.execute('SELECT count(*) FROM managed_deposit_returns').fetchone() == (0,)
    assert migrate(path) is None


def test_migration_19_copie_et_sauvegarde_preservent_ventes(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE payment_methods')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version IN (19,20)')
        db.execute("INSERT INTO managed_sales (id, reference, request_key, request_fingerprint, created_at, mode, total, payment_method) VALUES (1, 'V', 'v', 'x', '2025-01-01', 'retail', 100, 'wave')")
    backup = migrate(path)
    with sqlite3.connect(backup) as saved:
        assert saved.execute('SELECT payment_method, total FROM managed_sales').fetchone() == ('wave', 100)
        assert saved.execute("SELECT count(*) FROM sqlite_master WHERE name='payment_methods'").fetchone()[0] == 0
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT payment_method, total FROM managed_sales').fetchone() == ('wave', 100)
        assert db.execute("SELECT label, active FROM payment_methods WHERE code='wave'").fetchone() == ('Wave', 1)
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)


def test_migration_20_retours_vides_conserves_et_sauvegarde(tmp_path):
    path = tmp_path / 'depot.db'
    make_db(path)
    migrate(path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TABLE managed_deposit_return_recaptures')
        db.execute('DROP TABLE managed_deposit_return_cancellations')
        db.execute('DELETE FROM depotpro_schema_migrations WHERE version=20')
    backup = migrate(path)
    with sqlite3.connect(backup) as db:
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (19,)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT max(version) FROM depotpro_schema_migrations').fetchone() == (20,)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name IN ('managed_deposit_return_recaptures','managed_deposit_return_cancellations')").fetchone() == (2,)
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
