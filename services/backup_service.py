import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from config import DATA_DIR, DATABASE_URL


class BackupService:
    @staticmethod
    def get_backup_dir() -> Path:
        backup_dir = DATA_DIR / "Sauvegardes"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    @staticmethod
    def create_backup() -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"depotpro_backup_{timestamp}.db"
        backup_path = BackupService.get_backup_dir() / backup_filename
        
        if DATABASE_URL.startswith('sqlite:///'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
            shutil.copy2(db_path, str(backup_path))
        
        return backup_path
    
    @staticmethod
    def list_backups() -> list:
        backup_dir = BackupService.get_backup_dir()
        backups = []
        for file in backup_dir.glob('depotpro_backup_*.db'):
            stat = file.stat()
            backups.append({
                'path': file,
                'name': file.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime)
            })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    @staticmethod
    def restore_backup(backup_path: Path) -> bool:
        if DATABASE_URL.startswith('sqlite:///'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
            try:
                shutil.copy2(str(backup_path), db_path)
                return True
            except Exception as e:
                print(f"Erreur de restauration: {e}")
                return False
        return False