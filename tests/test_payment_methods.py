import pytest
from models.managed_operations import ManagedCashTransaction
from services.cash_methods import PaymentMethodService, labels
from services.deposit_configuration_service import DepositConfigurationService
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import PackagingService
from services.product_service import ProductService
from services.sale_cancellation_service import SaleCancellationService


def test_moyen_versionne_vente_annulation_et_desactivation(db_session):
    methods = PaymentMethodService(db_session)
    old = methods.create('Compte dépôt')
    cash = ManagedCashService(db_session)
    session = cash.open(0, 'caisse')
    product_service = ProductService(db_session)
    category = product_service.create_category('Boissons')
    product = product_service.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 2})
    pack = PackagingService(db_session).save(product.id, {'name': 'bouteille', 'coefficient': 1, 'retail_price': 500})
    DepositConfigurationService(db_session).configure(pack.id, 'none', [])
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', old, [{'packaging_id': pack.id, 'quantity': 1}], 'vente')
    new = methods.rename(old, 'Compte nouveau')
    assert labels(db_session)[old] == 'Compte dépôt'
    assert old not in labels(db_session, active_only=True) and labels(db_session, active_only=True)[new] == 'Compte nouveau'
    with pytest.raises(ValueError, match='actif'):
        ManagedSaleService(db_session).sell(session.id, 'retail', old, [{'packaging_id': pack.id, 'quantity': 1}], 'vente2')
    # Rejouer la même requête reste idempotent même après désactivation.
    assert ManagedSaleService(db_session).sell(session.id, 'retail', old, [{'packaging_id': pack.id, 'quantity': 1}], 'vente').id == sale.id
    SaleCancellationService(db_session).cancel(sale.id, session.id, 'Erreur', 'annulation', goods_recovered=True)
    refund = db_session.query(ManagedCashTransaction).filter_by(kind='outflow').one()
    assert refund.method == old and refund.amount == 500
    methods.deactivate(new)
    with pytest.raises(ValueError, match='espèces'):
        methods.deactivate('cash')


def test_doublons_et_erreurs_sans_modification(db_session):
    service = PaymentMethodService(db_session)
    code = service.create('Portefeuille')
    with pytest.raises(ValueError, match='existe'):
        service.create(' portefeuille ')
    with pytest.raises(ValueError, match='existe'):
        service.rename(code, 'Espèces')
    assert labels(db_session, active_only=True)[code] == 'Portefeuille'


def test_creation_concurrente_meme_nom(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    engine = create_engine(f'sqlite:///{tmp_path / "methods.db"}', connect_args={'timeout': 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    barrier = Barrier(2)
    def create(_):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                PaymentMethodService(db).create('Compte identique')
                return True
            except ValueError as exc:
                assert 'existe' in str(exc)
                return False
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(create, range(2))) == [False, True]
        with factory() as db:
            assert len(labels(db, active_only=True)) == 1
    finally:
        engine.dispose()
