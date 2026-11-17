"""Restaure une sauvegarde SQLite après arrêt complet de DEPOTPRO."""
import argparse
import sqlite3
from contextlib import closing
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DB_PATH


def restore(source_path: Path, destination_path: Path, *, allow_schema_change: bool = False) -> Path:
    source_path = source_path.resolve()
    destination_path = destination_path.resolve()
    if not source_path.is_file() or not destination_path.is_file():
        raise ValueError('La sauvegarde et la base à remplacer doivent exister.')
    if source_path == destination_path:
        raise ValueError('La sauvegarde et la base à remplacer doivent être différentes.')
    safety_path = destination_path.with_name(
        f'{destination_path.stem}_avant_restauration_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}.db'
    )
    with closing(sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)) as source:
        if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('La sauvegarde est corrompue.')
        tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'products', 'sales', 'users'}.issubset(tables):
            raise ValueError('La sauvegarde ne contient pas les tables DEPOTPRO attendues.')
        # Refuser les sauvegardes d'un autre schéma plutôt que de rendre
        # l'application inutilisable ou perdre des tables sans avertissement.
        with closing(sqlite3.connect(destination_path.as_uri() + '?mode=ro', uri=True)) as current:
            current_tables = {row[0] for row in current.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            backup_tables = {name for name in tables if not name.startswith('sqlite_')}
            if current_tables != backup_tables and not allow_schema_change:
                raise ValueError('Le schéma de la sauvegarde ne correspond pas à la base actuelle (tables).')
            for table in current_tables & backup_tables:
                quoted = table.replace('"', '""')
                current_columns = {row[1] for row in current.execute(f'PRAGMA table_info("{quoted}")')}
                backup_columns = {row[1] for row in source.execute(f'PRAGMA table_info("{quoted}")')}
                if current_columns != backup_columns and not allow_schema_change:
                    raise ValueError(f'Le schéma de la sauvegarde ne correspond pas à la table {table}.')
            try:
                with closing(sqlite3.connect(safety_path)) as safety:
                    current.backup(safety)
                    if safety.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise ValueError('La sauvegarde de sécurité est invalide.')
            except Exception:
                safety_path.unlink(missing_ok=True)
                raise
        # L'API SQLite remplace la base transactionnellement et gère son WAL ;
        # ne jamais remplacer le fichier avec shutil.copy pendant qu'il est ouvert.
        with closing(sqlite3.connect(destination_path, timeout=5)) as target:
            source.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError(f'Restauration invalide ; sauvegarde préalable : {safety_path}')
    return safety_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path, help='Fichier de sauvegarde à restaurer')
    parser.add_argument('--application-arretee', action='store_true',
                        help='Confirme que DEPOTPRO et tous les accès à la base sont arrêtés')
    parser.add_argument('--schema-different', action='store_true', help='Autoriser explicitement une restauration interversions (perte des changements depuis la sauvegarde)')
    args = parser.parse_args()
    if not args.application_arretee:
        parser.error('Arrêtez DEPOTPRO et tous les accès à la base, puis confirmez avec --application-arretee.')
    try:
        safety = restore(args.backup, DB_PATH, allow_schema_change=args.schema_different)
    except (sqlite3.Error, ValueError, OSError) as exc:
        parser.exit(1, f'Restauration impossible : {exc}\n')
    print(f'Restauration terminée. Sauvegarde préalable : {safety}')


if __name__ == '__main__':
    main()
