"""Contrôle sans modification des montants d'une base SQLite existante."""
import argparse
import sqlite3
import sys
from pathlib import Path

# Exécution directe : python scripts/audit_fcfa.py /chemin/depot.db
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database import Base
import models  # noqa: F401
from money import CFAAmount, fcfa


def audit(path):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    problems = []
    with sqlite3.connect(uri, uri=True) as db:
        existing = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in Base.metadata.sorted_tables:
            if table.name not in existing:
                continue
            columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table.name}")')}
            for column in table.columns:
                if not isinstance(column.type, CFAAmount) or column.name not in columns:
                    continue
                for rowid, value in db.execute(f'SELECT rowid, "{column.name}" FROM "{table.name}" WHERE "{column.name}" IS NOT NULL'):
                    try:
                        fcfa(value)
                    except ValueError:
                        problems.append((table.name, rowid, column.name, value))
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', help='Chemin vers la base SQLite à auditer')
    args = parser.parse_args()
    try:
        problems = audit(args.database)
    except sqlite3.Error as exc:
        parser.exit(2, f'Impossible de lire la base : {exc}\n')
    for table, rowid, column, value in problems:
        print(f'{table} ligne {rowid}, {column} : {value!r}')
    if problems:
        print(f'{len(problems)} montant(s) non entiers ou invalides ; aucune donnée modifiée.')
        return 1
    print('Aucun montant fractionnaire ou invalide détecté dans les colonnes présentes.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
