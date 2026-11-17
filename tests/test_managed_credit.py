from services.deposit_configuration_service import DepositConfigurationService
import pytest
from sqlalchemy import event
from models.client import Client
from models.debt import ClientDebt
from models.managed_credit import ManagedCreditSale, ManagedCreditPayment
from models.managed_operations import ManagedCashTransaction, ManagedSale, ManagedSalePayment
from models.product import Product
from services.managed_credit_service import ManagedCreditService
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import PackagingService
from services.product_service import ProductService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Test')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 48})
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000})
    DepositConfigurationService(db_session).configure(pack.id, 'none', [])
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    client = ManagedCreditService(db_session).create_client('Client test', client_type='professionnel', credit_limit=5000)
    return product, pack, cash, session, client


def test_credit_mixte_et_reglements_idempotents(db_session, scenario):
    product, pack, cash, session, client = scenario
    service = ManagedSaleService(db_session)
    lines = [{'packaging_id': pack.id, 'quantity': 1}]
    payments = [{'method': 'cash', 'amount': 500}, {'method': 'wave', 'amount': 1000}]
    sale = service.sell(session.id, 'retail', 'credit', lines, 'vente-credit', payments=payments, client_id=client.id)
    assert service.sell(session.id, 'retail', 'credit', lines, 'vente-credit', payments=list(reversed(payments)), client_id=client.id).id == sale.id
    credit = db_session.query(ManagedCreditSale).one()
    assert (credit.initial_amount, credit.remaining_amount) == (1500, 1500)
    assert product.stock_quantity == 24 and cash.cash_available(session) == 1500
    assert cash.flows(session.id) == {'cash': {'in': 500, 'out': 0}, 'wave': {'in': 1000, 'out': 0}}
    settlements = ManagedCreditService(db_session)
    p = settlements.pay(credit.id, session.id, 'wave', 1000, 'p1')
    assert settlements.pay(credit.id, session.id, 'wave', 1000, 'p1').id == p.id
    with pytest.raises(ValueError, match='dépasse'):
        settlements.pay(credit.id, session.id, 'cash', 501, 'surplus')
    settlements.pay(credit.id, session.id, 'cash', 500, 'p2')
    assert credit.remaining_amount == 0 and cash.cash_available(session) == 2000
    assert db_session.query(ManagedCreditPayment).count() == 2
    assert db_session.query(ManagedSalePayment).count() == 4
    assert cash.flows(session.id) == {'cash': {'in': 1000, 'out': 0}, 'wave': {'in': 2000, 'out': 0}}


def test_credit_sans_paiement_et_plafond_confirmation(db_session, scenario):
    product, pack, cash, session, client = scenario
    lines = [{'packaging_id': pack.id, 'quantity': 1}]
    service = ManagedSaleService(db_session)
    service.sell(session.id, 'retail', 'credit', lines, 's1', payments=[], client_id=client.id)
    with pytest.raises(ValueError, match='Plafond'):
        service.sell(session.id, 'retail', 'credit', lines, 's2', payments=[], client_id=client.id)
    assert product.stock_quantity == 24 and cash.cash_available(session) == 1000
    service.sell(session.id, 'retail', 'credit', lines, 's2', payments=[], client_id=client.id, override_limit=True)
    assert product.stock_quantity == 0 and db_session.query(ManagedCreditSale).count() == 2
    assert db_session.query(ManagedCashTransaction).count() == 0


def test_credit_refuse_trop_percu_ou_client_non_rapproche(db_session, scenario):
    product, pack, cash, session, client = scenario
    service = ManagedSaleService(db_session)
    lines = [{'packaging_id': pack.id, 'quantity': 1}]
    for amount in (3000, 3001):
        with pytest.raises(ValueError, match='solde restant'):
            service.sell(session.id, 'retail', 'credit', lines, f'bad-{amount}', payments=[{'method': 'wave', 'amount': amount}], client_id=client.id)
    db_session.add(ClientDebt(reference='D-OLD', client_id=client.id, initial_amount=100, remaining_amount=100))
    db_session.commit()
    with pytest.raises(ValueError, match='non rapproché'):
        service.sell(session.id, 'retail', 'credit', lines, 'historique', payments=[], client_id=client.id)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0


def test_echec_caisse_annule_vente_credit_et_stock(db_session, scenario):
    product, pack, cash, session, client = scenario
    def fail(_mapper, _connection, target):
        if target.kind == 'sale':
            raise RuntimeError('échec caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échec caisse'):
            ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}], 's',
                payments=[{'method': 'cash', 'amount': 500}], client_id=client.id)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedCreditSale).count() == db_session.query(ManagedSale).count() == 0


def test_reglements_concurrents_sans_depassement(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    engine = create_engine(f'sqlite:///{tmp_path / "credit-concurrent.db"}', connect_args={'timeout': 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    from models.payment_method import PaymentMethod
    from services.cash_methods import METHODS
    with factory() as seed:
        seed.add_all(PaymentMethod(code=k, label=v, active=True) for k, v in METHODS.items())
        seed.commit()
    with factory() as db:
        products = ProductService(db)
        category = products.create_category('Test')
        product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 1})
        pack = PackagingService(db).save(product.id, {'name': 'bouteille', 'coefficient': 1, 'retail_price': 1500})
        DepositConfigurationService(db).configure(pack.id, 'none', [])
        session = ManagedCashService(db).open(0, 'open')
        client = ManagedCreditService(db).create_client('Client', client_type='particulier', no_limit=True)
        ManagedSaleService(db).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}], 'sale', payments=[], client_id=client.id)
        credit_id, session_id = db.query(ManagedCreditSale).one().id, session.id
    barrier = Barrier(2)
    def pay(key):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                ManagedCreditService(db).pay(credit_id, session_id, 'cash', 1000, key)
                return True
            except ValueError as exc:
                assert 'dépasse' in str(exc)
                return False
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(pay, ('p1', 'p2'))) == [False, True]
        with factory() as db:
            assert db.get(ManagedCreditSale, credit_id).remaining_amount == 500
            assert db.query(ManagedCreditPayment).count() == 1
            assert db.query(ManagedCashTransaction).count() == 1
    finally:
        engine.dispose()


def test_annulation_credit_mixte_avec_reglements_et_historique(db_session, scenario):
    from models.managed_operations import ManagedSaleCancellation, ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session, client = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}],
        'credit', payments=[{'method': 'cash', 'amount': 500}, {'method': 'wave', 'amount': 1000}], client_id=client.id)
    credit = db_session.query(ManagedCreditSale).one()
    ManagedCreditService(db_session).pay(credit.id, session.id, 'wave', 500, 'reglement')
    service = SaleCancellationService(db_session)
    cancellation = service.cancel(sale.id, session.id, 'Retour complet', 'ann', goods_recovered=True)
    assert service.cancel(sale.id, session.id, 'Retour complet', 'ann', goods_recovered=True).id == cancellation.id
    assert credit.initial_amount == 1500 and credit.remaining_amount == 0
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert cash.flows(session.id) == {'cash': {'in': 500, 'out': 500}, 'wave': {'in': 1500, 'out': 1500}}
    assert db_session.query(ManagedSale).count() == 1
    assert db_session.query(ManagedCreditPayment).count() == 1
    assert db_session.query(ManagedSaleRefund).count() == 3
    assert db_session.query(ManagedSaleCancellation).count() == 1
    with pytest.raises(ValueError, match='annulée'):
        ManagedCreditService(db_session).pay(credit.id, session.id, 'cash', 1, 'reglement-apres')
    with pytest.raises(ValueError, match='déjà annulée'):
        service.cancel(sale.id, session.id, 'Autre', 'ann2', goods_recovered=True)


def test_annulation_credit_sans_acompte_ni_reglement(db_session, scenario):
    from models.managed_operations import ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session, client = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}],
        'credit', payments=[], client_id=client.id)
    credit = db_session.query(ManagedCreditSale).one()
    SaleCancellationService(db_session).cancel(sale.id, session.id, 'Marchandise reprise', 'ann', goods_recovered=True)
    assert credit.remaining_amount == 0 and product.stock_quantity == 48
    assert cash.cash_available(session) == 1000 and db_session.query(ManagedSaleRefund).count() == 0


def test_annulation_credit_echec_rollback_et_historique_incoherent(db_session, scenario):
    from models.managed_operations import ManagedSaleCancellation, ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session, client = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}],
        'credit', payments=[{'method': 'cash', 'amount': 500}], client_id=client.id)
    credit = db_session.query(ManagedCreditSale).one()
    cash.record(session.id, 'outflow', 'cash', 1500, 'Sortie manuelle', 'sortie')
    with pytest.raises(ValueError, match='insuffisantes'):
        SaleCancellationService(db_session).cancel(sale.id, session.id, 'Retour complet', 'ann', goods_recovered=True)
    assert credit.remaining_amount == 2500 and product.stock_quantity == 24
    assert db_session.query(ManagedSaleCancellation).count() == db_session.query(ManagedSaleRefund).count() == 0
