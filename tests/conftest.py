import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, engine

TEST_DB_URL = "sqlite:///./test_depot.db"
TEST_ENGINE = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TEST_SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function", autouse=True)
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TEST_SESSION_LOCAL()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        if os.path.exists("./test_depot.db"):
            os.remove("./test_depot.db")


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """Ensure clean state between tests."""
    yield
    session = TEST_SESSION_LOCAL()
    session.rollback()
    session.close()
