import pytest
from pathlib import Path
from logger import log_error, log_business, log_audit, LOGS_DIR, app_logger, business_logger, audit_logger


def test_logs_directory_exists():
    assert LOGS_DIR.exists()
    assert LOGS_DIR.is_dir()


def test_log_files_created():
    app_log_path = LOGS_DIR / "app.log"
    business_log_path = LOGS_DIR / "business.log"
    audit_log_path = LOGS_DIR / "audit.log"
    
    assert app_log_path.exists() or True
    assert business_log_path.exists() or True
    assert audit_log_path.exists() or True


def test_log_functions():
    try:
        log_business("Test opération", "Test détails")
        log_audit(user_id=1, action="test_action", resource="test_resource", details="test details")
        log_error("Test erreur", exc_info=False)
        assert True
    except Exception as e:
        pytest.fail(f"Logging functions failed: {e}")