import pytest
from models.product import Product
from models.returnable_packaging import ReturnablePackagingType
from services.returnable_packaging_service import ReturnablePackagingService


def test_catalogue_sans_valeur_inventee_ni_mouvement(db_session):
    service = ReturnablePackagingService(db_session)
    before = db_session.query(Product).count()
    bottle = service.create(code='B-1', name='Bouteille', producer='Brasseur test', kind='bottle')
    crate = service.create(code='C-1', name='Casier', producer='Brasseur test', kind='crate',
                           description='Format confirmé', deposit_value='0')
    assert bottle.deposit_value is None and crate.deposit_value == 0
    assert db_session.query(Product).count() == before
    assert len(service.list()) == 2
    service.archive(bottle.id)
    assert [i.id for i in service.list()] == [crate.id]
    assert db_session.get(ReturnablePackagingType, bottle.id) is not None


def test_catalogue_validation(db_session):
    service = ReturnablePackagingService(db_session)
    args = dict(code='A', name='Casier', producer='Brasseur', kind='crate')
    service.create(**args)
    with pytest.raises(ValueError, match='existe'):
        service.create(**{**args, 'code': 'a'})
    for fields in ({'code': ''}, {'producer': ''}, {'kind': 'pack'},
                   {'deposit_value': '-1'}, {'deposit_value': '1.5'}):
        with pytest.raises(ValueError):
            service.create(**{**args, 'code': 'B', **fields})
    assert db_session.query(ReturnablePackagingType).count() == 1
