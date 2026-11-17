import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_premier_demarrage_sans_compte_par_defaut(tmp_path):
    env = os.environ.copy()
    env['HOME'] = str(tmp_path)
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    path = tmp_path / 'DepotPro_Data' / 'depot.db'
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT count(*) FROM users').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM owner_security').fetchone()[0] == 0
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(i,) for i in range(1, 21)]


def test_base_existante_non_migree_refusee_sans_modification(tmp_path):
    path = tmp_path / 'DepotPro_Data' / 'depot.db'
    path.parent.mkdir()
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE historique (valeur TEXT)')
        db.execute("INSERT INTO historique VALUES ('intact')")
    env = os.environ.copy()
    env['HOME'] = str(tmp_path)
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'non migrée' in result.stderr
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT valeur FROM historique').fetchone()[0] == 'intact'
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='users'").fetchone()[0] == 0


def _init_tmp(tmp_path):
    env = os.environ.copy()
    env['HOME'] = str(tmp_path)
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return env, root, tmp_path / 'DepotPro_Data' / 'depot.db'


def test_demarrage_refuse_index_unique_caisse_absent_sans_reparation(tmp_path):
    env, root, path = _init_tmp(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('DROP INDEX uq_managed_cash_open')
        db.execute("INSERT INTO categories (id, name) VALUES (1, 'Historique')")
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Index de session de caisse unique absent' in result.stderr
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT name FROM categories').fetchone() == ('Historique',)
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='uq_managed_cash_open'").fetchone() == (0,)


def test_demarrage_refuse_cle_etrangere_invalide(tmp_path):
    env, root, path = _init_tmp(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute("INSERT INTO stock_movements (product_id, movement_type) VALUES (999999, 'historique')")
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Clés étrangères incohérentes' in result.stderr
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT product_id FROM stock_movements').fetchone() == (999999,)


def test_demarrage_refuse_index_caisse_de_mauvaise_definition(tmp_path):
    env, root, path = _init_tmp(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('DROP INDEX uq_managed_cash_open')
        db.execute("CREATE UNIQUE INDEX uq_managed_cash_open ON managed_cash_sessions(status) WHERE status = 'closed'")
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Index de session de caisse unique incompatible' in result.stderr
    with sqlite3.connect(path) as db:
        assert "'closed'" in db.execute("SELECT sql FROM sqlite_master WHERE name='uq_managed_cash_open'").fetchone()[0]


def test_demarrage_refuse_protection_code_barres_manquante(tmp_path):
    env, root, path = _init_tmp(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute('DROP TRIGGER barcode_products_insert_guard')
    result = subprocess.run([sys.executable, 'init_db.py'], cwd=root, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Protection de code-barres absente' in result.stderr
