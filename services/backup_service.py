"""Sauvegarde SQLite cohérente, y compris les données présentes dans le WAL."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from config import DATA_DIR, DB_PATH
from logger import log_business, log_error


class BackupService:
    @staticmethod
    def get_backup_dir() -> Path:
        backup_dir = DATA_DIR / 'Sauvegardes'
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    @staticmethod
    def create_backup() -> Path:
        if not DB_PATH.is_file():
            raise FileNotFoundError(f'Base de données introuvable : {DB_PATH}')
        filename = f"depotpro_backup_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}.db"
        destination = BackupService.get_backup_dir() / filename
        try:
            # mode=ro empêche la création accidentelle d'une base vide.
            with closing(sqlite3.connect(DB_PATH.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(destination)) as target:
                    source.backup(target)
                    if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise ValueError('La sauvegarde a échoué au contrôle d’intégrité')
            log_business('Création sauvegarde', f'Sauvegarde créée : {filename}')
            return destination
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    @staticmethod
    def list_backups() -> list:
        backups = []
        for file in BackupService.get_backup_dir().glob('depotpro_backup_*.db'):
            stat = file.stat()
            backups.append({'path': file, 'name': file.name, 'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_mtime)})
        return sorted(backups, key=lambda x: x['created'], reverse=True)

    @staticmethod
    def restore_backup(backup_path: Path) -> bool:
        # Une session SQLAlchemy active peut conserver des objets périmés après une
        # restauration. La restauration doit être exécutée hors application.
        log_error('Restauration en ligne désactivée : arrêter DEPOTPRO et utiliser scripts/restore_backup.py', exc_info=False)
        return False
