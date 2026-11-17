import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database import Base
import models  # noqa: F401


@pytest.fixture(scope='function')
def db_session():
    engine = create_engine('sqlite:///:memory:')

    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    from models.payment_method import PaymentMethod
    from services.cash_methods import METHODS
    session.add_all(PaymentMethod(code=k, label=v, active=True) for k, v in METHODS.items())
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
