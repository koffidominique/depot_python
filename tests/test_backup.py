import sqlite3

import pytest

from scripts.restore_backup import restore
from services import backup_service
from services.backup_service import BackupService


def init_database(path):
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('PRAGMA wal_autocheckpoint=0')
    for table in ('products', 'sales', 'users'):
        connection.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY, value TEXT)')
    connection.commit()
    return connection


def test_sauvegarde_inclut_wal_et_noms_uniques(tmp_path, monkeypatch):
    path = tmp_path / 'current.db'
    db = init_database(path)
    db.execute("INSERT INTO products VALUES (1, 'dans le WAL')")
    db.commit()
    assert (tmp_path / 'current.db-wal').exists()
    monkeypatch.setattr(backup_service, 'DB_PATH', path)
    monkeypatch.setattr(BackupService, 'get_backup_dir', lambda: tmp_path / 'backups')
    (tmp_path / 'backups').mkdir()
    first = BackupService.create_backup()
    second = BackupService.create_backup()
    assert first != second
    with sqlite3.connect(first) as result:
        assert result.execute('SELECT value FROM products').fetchone() == ('dans le WAL',)
    db.close()


def test_restauration_et_sauvegarde_preventive(tmp_path):
    target = tmp_path / 'current.db'
    backup = tmp_path / 'backup.db'
    for path, value in ((target, 'avant'), (backup, 'restauré')):
        db = init_database(path)
        db.execute('INSERT INTO products VALUES (1, ?)', (value,))
        db.commit()
        db.close()
    safety = restore(backup, target)
    with sqlite3.connect(target) as db:
        assert db.execute('SELECT value FROM products').fetchone()[0] == 'restauré'
    with sqlite3.connect(safety) as db:
        assert db.execute('SELECT value FROM products').fetchone()[0] == 'avant'


def test_restauration_refuse_fichier_invalide_sans_modifier_base(tmp_path):
    target = tmp_path / 'current.db'
    db = init_database(target)
    db.execute("INSERT INTO products VALUES (1, 'avant')")
    db.commit()
    db.close()
    invalid = tmp_path / 'bad.db'
    invalid.write_text('pas une base')
    with pytest.raises(sqlite3.DatabaseError):
        restore(invalid, target)
    with sqlite3.connect(target) as db:
        assert db.execute('SELECT value FROM products').fetchone()[0] == 'avant'


def test_restauration_en_ligne_desactivee(tmp_path):
    assert BackupService.restore_backup(tmp_path / 'unused.db') is False


def test_restauration_refuse_schema_different(tmp_path):
    target = tmp_path / 'current.db'
    backup = tmp_path / 'old.db'
    current = init_database(target)
    current.execute('CREATE TABLE important (id INTEGER)')
    current.commit()
    current.close()
    init_database(backup).close()
    with pytest.raises(ValueError, match='schéma'):
        restore(backup, target)
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='important'").fetchone()[0] == 1
