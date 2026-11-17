from pathlib import Path
from datetime import datetime

APP_NAME = "DEPOTPRO ERP"
APP_VERSION = "1.0.0"

DATA_DIR = Path.home() / "DepotPro_Data"
DB_PATH = DATA_DIR / "depot.db"
DB_URL = f"sqlite:///{DB_PATH}"

FOLDERS = [
    DATA_DIR,
    DATA_DIR / "Factures",
    DATA_DIR / "Bons_Commande",
    DATA_DIR / "Bons_Livraison",
    DATA_DIR / "Reçus",
    DATA_DIR / "Exports",
    DATA_DIR / "Backups",
    DATA_DIR / "Logs",
    DATA_DIR / "Images"
]

DEFAULT_CURRENCY = "FCFA"
DEFAULT_TAX_RATE = 0.0

def init_data_dir():
    for folder in FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)

init_data_dir()