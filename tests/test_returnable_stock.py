import pytest
from models.returnable_stock import ReturnableStockMovement
from services.returnable_packaging_service import ReturnablePackagingService
from services.returnable_stock_service import ReturnableStockService


@pytest.fixture
def item(db_session):
    return ReturnablePackagingService(db_session).create(code='VIDE', name='Casier test', producer='Circuit test', kind='crate')


def test_initial_explicit_et_journal_idempotent(db_session, item):
    service = ReturnableStockService(db_session)
    assert service.balance(item.id) is None
    first = service.record(item.id, 'initial', 10, 'Comptage', 'initial')
    assert (first.stock_before, first.stock_after) == (None, 10)
    assert service.record(item.id, 'initial', 10, 'Comptage', 'initial').id == first.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        service.record(item.id, 'initial', 11, 'Comptage', 'initial')
    with pytest.raises(ValueError, match='déjà été déclaré'):
        service.record(item.id, 'initial', 10, 'Comptage', 'autre')
    movement = service.record(item.id, 'breakage', 2, 'Casse', 'casse', 'BON-1')
    assert (movement.quantity, movement.stock_before, movement.stock_after) == (-2, 10, 8)
    service.record(item.id, 'entry', 3, 'Retour de vides', 'entree')
    assert service.balance(item.id) == 11
    assert len(service.history(item.id)) == 3
    assert db_session.query(ReturnableStockMovement).count() == 3


def test_refus_absence_initial_stock_negatif_et_saisie(db_session, item):
    service = ReturnableStockService(db_session)
    with pytest.raises(ValueError, match='initial'):
        service.record(item.id, 'entry', 1, 'Motif', 'a')
    for value in ('0.5', -1, 'NaN', True, ''):
        with pytest.raises(ValueError, match='entier'):
            service.record(item.id, 'initial', value, 'Motif', 'initial')
    service.record(item.id, 'initial', 0, 'Comptage', 'zero')
    with pytest.raises(ValueError, match='résultante'):
        service.record(item.id, 'exit', 1, 'Livraison', 'sortie')
    with pytest.raises(ValueError, match='motif'):
        service.record(item.id, 'entry', 1, '', 'entree')
    assert service.balance(item.id) == 0
    assert len(service.history(item.id)) == 1


def test_pas_archiver_stock_non_nul(db_session, item):
    stock = ReturnableStockService(db_session)
    catalogue = ReturnablePackagingService(db_session)
    stock.record(item.id, 'initial', 1, 'Comptage', 'i')
    with pytest.raises(ValueError, match='non nul'):
        catalogue.archive(item.id)
    stock.record(item.id, 'exit', 1, 'Départ', 's')
    catalogue.archive(item.id)
    with pytest.raises(ValueError, match='actif'):
        stock.record(item.id, 'entry', 1, 'Retour', 'e')
    assert len(stock.history(item.id)) == 2


def test_sessions_longues_necrasent_pas_le_stock(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    engine = create_engine(f'sqlite:///{tmp_path / "stock.db"}')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    first, second = factory(), factory()
    try:
        item = ReturnablePackagingService(first).create(code='C', name='Casier', producer='Circuit', kind='crate')
        item_id = item.id
        stock1, stock2 = ReturnableStockService(first), ReturnableStockService(second)
        stock1.record(item_id, 'initial', 10, 'Comptage', 'init')
        assert stock2.balance(item_id) == 10
        stock1.record(item_id, 'exit', 7, 'Sortie', 's1')
        with pytest.raises(ValueError, match='résultante'):
            stock2.record(item_id, 'exit', 5, 'Sortie', 's2')
        assert stock2.balance(item_id) == 3
    finally:
        first.close()
        second.close()
        engine.dispose()
