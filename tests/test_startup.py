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
        assert db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version').fetchall() == [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,), (10,)]


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
