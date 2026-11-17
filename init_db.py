"""Initialisation sans identifiant par défaut ni migration silencieuse."""
import sqlite3
from contextlib import closing
from config import DB_PATH
from database import Base, engine
import models  # noqa: F401
from scripts.migrate_database import migrate, VERSION
from services.schema_validation import validate_schema


def initialize_database():
    existed = DB_PATH.exists()
    if not existed:
        Base.metadata.create_all(bind=engine)
        engine.dispose()
        migrate(DB_PATH)
    with closing(sqlite3.connect(DB_PATH.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'depotpro_schema_migrations' not in tables:
            raise RuntimeError('Base existante non migrée. Arrêtez l’application, sauvegardez-la et exécutez python scripts/migrate_database.py --application-arretee.')
        versions = [row[0] for row in db.execute('SELECT version FROM depotpro_schema_migrations ORDER BY version')]
        if versions != list(range(1, VERSION + 1)):
            raise RuntimeError('Base nécessitant une migration. Arrêtez l’application puis exécutez python scripts/migrate_database.py --application-arretee.')
        try:
            validate_schema(db)
        except (sqlite3.Error, ValueError) as exc:
            raise RuntimeError(f'Base incohérente ou incomplète : {exc} Ne modifiez pas les données sans sauvegarde et diagnostic.') from exc


if __name__ == '__main__':
    initialize_database()
