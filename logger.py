import logging
import sys
from pathlib import Path
from datetime import datetime
from config import DATA_DIR

LOGS_DIR = DATA_DIR / "Logs"

def setup_logger(name, log_file, level=logging.INFO, format_str=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(LOGS_DIR / log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        
        if not format_str:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        else:
            formatter = logging.Formatter(format_str)
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

app_logger = setup_logger('app', 'app.log', level=logging.ERROR)
business_logger = setup_logger('business', 'business.log', level=logging.INFO)
audit_logger = setup_logger('audit', 'audit.log', level=logging.INFO)

def log_error(message, exc_info=True):
    app_logger.error(message, exc_info=exc_info)

def log_business(operation, details):
    business_logger.info(f"{operation} - {details}")

def log_audit(user_id, action, resource=None, details=None):
    audit_logger.info(f"USER:{user_id} - ACTION:{action} - RESOURCE:{resource or 'N/A'} - DETAILS:{details or 'N/A'}")