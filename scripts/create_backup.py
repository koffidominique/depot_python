"""Crée une sauvegarde cohérente de la base DEPOTPRO."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.backup_service import BackupService

if __name__ == '__main__':
    try:
        print(f'Sauvegarde créée : {BackupService.create_backup()}')
    except Exception as exc:
        sys.exit(f'Sauvegarde impossible : {exc}')
