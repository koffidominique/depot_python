import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.owner_security import OwnerSecurity
from services.owner_auth_service import OwnerAuthService, PinLocked


@pytest.fixture
def auth(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "auth.db"}')
    OwnerSecurity.__table__.create(engine)
    factory = sessionmaker(bind=engine)
    service = OwnerAuthService(factory, clock=lambda: 1000)
    yield service, factory
    engine.dispose()


def test_initialisation_pin_et_hash(auth):
    service, factory = auth
    assert not service.is_configured()
    with pytest.raises(ValueError):
        service.setup_pin('1234', '1234')
    with pytest.raises(ValueError):
        service.setup_pin('123456', '123457')
    service.setup_pin('123456', '123456')
    assert service.is_configured()
    with factory() as db:
        hashed = db.get(OwnerSecurity, 1).pin_hash
        assert hashed != '123456'
        assert bcrypt.checkpw(b'123456', hashed.encode())
    assert service.verify_pin('123456')
    with pytest.raises(ValueError):
        service.setup_pin('654321', '654321')


def test_limitation_persistante_et_modification(auth):
    service, factory = auth
    service.setup_pin('123456', '123456')
    for _ in range(3):
        assert service.verify_pin('000000') is False
    with pytest.raises(PinLocked):
        service.verify_pin('123456')
    service.clock = lambda: 1006
    assert service.verify_pin('123456')
    service.change_pin('123456', '654321', '654321')
    assert not service.verify_pin('123456')
    assert service.verify_pin('654321')
    service.set_inactivity_seconds(120)
    assert service.get_inactivity_seconds() == 120
    with pytest.raises(ValueError):
        service.set_inactivity_seconds(0)


def test_temporisation_progressive_et_persistante(auth):
    service, factory = auth
    service.setup_pin('123456', '123456')
    for _ in range(3):
        assert not service.verify_pin('000000')
    with pytest.raises(PinLocked) as locked:
        OwnerAuthService(factory, clock=lambda: 1001).verify_pin('123456')
    assert locked.value.seconds == 4
    service.clock = lambda: 1005
    assert not service.verify_pin('000000')
    with pytest.raises(PinLocked) as locked:
        service.verify_pin('123456')
    assert locked.value.seconds == 10
    service.clock = lambda: 1015
    assert service.verify_pin('123456')
    with factory() as db:
        assert db.get(OwnerSecurity, 1).failed_attempts == 0
