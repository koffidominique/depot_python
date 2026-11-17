import subprocess
import sys
from pathlib import Path
from typing import Optional
from logger import log_error, log_business


class PrintService:
    @staticmethod
    def print_file(file_path: Path) -> bool:
        if sys.platform == 'darwin':
            try:
                subprocess.run(['lpr', str(file_path)], check=True)
                log_business("Impression fichier", f"Fichier {file_path} imprimé avec succès")
                return True
            except Exception as e:
                log_error(f"Erreur d'impression du fichier {file_path}: {e}")
                return False
        elif sys.platform == 'win32':
            try:
                subprocess.run(['print', str(file_path)], shell=True, check=True)
                log_business("Impression fichier", f"Fichier {file_path} imprimé avec succès")
                return True
            except Exception as e:
                log_error(f"Erreur d'impression du fichier {file_path}: {e}")
                return False
        elif sys.platform.startswith('linux'):
            try:
                subprocess.run(['lp', str(file_path)], check=True)
                log_business("Impression fichier", f"Fichier {file_path} imprimé avec succès")
                return True
            except Exception as e:
                log_error(f"Erreur d'impression du fichier {file_path}: {e}")
                return False
        return False
    
    @staticmethod
    def open_file(file_path: Path) -> bool:
        import os
        import platform
        try:
            if platform.system() == 'Darwin':
                subprocess.run(['open', str(file_path)], check=True)
            elif platform.system() == 'Windows':
                os.startfile(str(file_path))
            else:
                subprocess.run(['xdg-open', str(file_path)], check=True)
            log_business("Ouverture fichier", f"Fichier {file_path} ouvert avec succès")
            return True
        except Exception as e:
            log_error(f"Erreur d'ouverture du fichier {file_path}: {e}")
            return False