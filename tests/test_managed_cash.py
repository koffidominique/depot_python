import pytest
from sqlalchemy import event
from models.cash import CashSession
from models.debt import SupplierDebt
from models.managed_cash import ManagedCashEntry, ManagedCashSession
from models.payment import Payment
from models.supplier import Supplier
from services.managed_cash_service import ManagedCashService
from services.purchase_service import PurchaseService, SupplierPaymentService
from services.product_service import ProductService
from services.packaging_service import PackagingService


@pytest.fixture
def debt(db_session):
    supplier = Supplier(code='F', name='Fournisseur', phone='01')
    db_session.add(supplier)
    db_session.commit()
    products = ProductService(db_session)
    category = products.create_category('Cat')
    product = products.create_product({'name': 'Boisson', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 0})
    pack = PackagingService(db_session).save(product.id, {'name': 'pack', 'coefficient': 6})
    purchases = PurchaseService(db_session)
    order = purchases.create_purchase_order({'supplier_id': supplier.id}, [{'packaging_id': pack.id, 'ordered_quantity': 2, 'unit_price': 1000}])
    purchases.validate_purchase_order(order.id)
    receipt = purchases.receive_purchase_order(order.id, [{'line_id': order.purchase_order_lines[0].id, 'received_quantity': 2}], request_key='rec')
    return db_session.query(SupplierDebt).filter_by(receipt_id=receipt.id).one()


def test_paiements_et_cloture_sans_double_comptage(db_session, debt):
    cash = ManagedCashService(db_session)
    session = cash.open(1500, 'ouvrir')
    assert cash.open(1500, 'ouvrir').id == session.id
    with pytest.raises(ValueError, match='déjà ouverte'):
        cash.open(1500, 'autre')
    pay = SupplierPaymentService(db_session)
    payment = pay.pay(debt.id, 700, 'cash', 'p1', cash_session_id=session.id)
    assert pay.pay(debt.id, 700, 'cash', 'p1', cash_session_id=session.id).id == payment.id
    pay.pay(debt.id, 500, 'mobile_money', 'p2', cash_session_id=session.id)
    assert cash.cash_available(session) == 800
    assert cash.totals(session.id) == {'cash': 700, 'mobile_money': 500}
    assert (debt.paid_amount, debt.remaining_amount, debt.supplier.balance_due) == (1200, 800, 800)
    assert db_session.query(ManagedCashEntry).count() == 2
    with pytest.raises(ValueError, match='commentaire'):
        cash.close(session.id, 799, '', 'fermer')
    assert cash.close(session.id, 799, 'Un franc manquant', 'fermer')
    assert cash.close(session.id, 799, 'Un franc manquant', 'fermer')
    assert (session.theoretical_cash, session.physical_cash, session.difference) == (800, 799, -1)
    assert pay.pay(debt.id, 700, 'cash', 'p1', cash_session_id=session.id).id == payment.id
    with pytest.raises(ValueError, match='ouverte'):
        pay.pay(debt.id, 100, 'cash', 'p3', cash_session_id=session.id)


def test_limites_et_absence_caisse_annulent_le_paiement(db_session, debt):
    service = SupplierPaymentService(db_session)
    cash = ManagedCashService(db_session)
    with pytest.raises(ValueError, match='session'):
        service.pay(debt.id, 10, 'cash', 'p0')
    session = cash.open(100, 'open')
    with pytest.raises(ValueError, match='insuffisantes'):
        service.pay(debt.id, 101, 'cash', 'p1', cash_session_id=session.id)
    with pytest.raises(ValueError, match='dépasse'):
        service.pay(debt.id, 2001, 'transfer', 'p2', cash_session_id=session.id)
    assert debt.remaining_amount == 2000 and debt.supplier.balance_due == 2000
    assert db_session.query(Payment).count() == 0
    assert db_session.query(ManagedCashEntry).count() == 0


def test_echec_ecriture_caisse_rollback_total(db_session, debt):
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    def fail(_mapper, _connection, _target):
        raise RuntimeError('échec simulé')
    event.listen(ManagedCashEntry, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='simulé'):
            SupplierPaymentService(db_session).pay(debt.id, 500, 'cash', 'pay', cash_session_id=session.id)
    finally:
        event.remove(ManagedCashEntry, 'before_insert', fail)
    assert debt.remaining_amount == debt.supplier.balance_due == 2000
    assert db_session.query(Payment).count() == db_session.query(ManagedCashEntry).count() == 0
    assert cash.cash_available(session) == 1000


def test_caisse_historique_ouverte_bloque_nouvelle_caisse(db_session):
    db_session.add(CashSession(status='open', initial_cash=100, theoretical_balance=100))
    db_session.commit()
    with pytest.raises(ValueError, match='ancienne caisse'):
        ManagedCashService(db_session).open(100, 'open')
    assert db_session.query(ManagedCashSession).count() == 0


def test_paiement_historique_non_rattache_et_suppression_bloquee(db_session, debt):
    from services.payment_service import PaymentService
    old = Payment(reference='REG-FOUR-old', supplier_debt_id=debt.id, amount=100, payment_method='cash', cash_link_status='outside_cash')
    db_session.add(old)
    db_session.commit()
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    with pytest.raises(ValueError, match='déjà été utilisée'):
        SupplierPaymentService(db_session).pay(debt.id, 100, 'cash', 'old', cash_session_id=session.id)
    with pytest.raises(ValueError, match='contrepassation'):
        PaymentService(db_session).delete_payment(old.id)
    assert old.cash_link_status == 'outside_cash'
    assert db_session.query(ManagedCashEntry).count() == 0


def test_deux_sessions_nepeuvent_pas_depaisser_stock_perime(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    engine = create_engine(f'sqlite:///{tmp_path / "caisse.db"}')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    from models.payment_method import PaymentMethod
    from services.cash_methods import METHODS
    with factory() as seed:
        seed.add_all(PaymentMethod(code=k, label=v, active=True) for k, v in METHODS.items())
        seed.commit()
    a, b = factory(), factory()
    try:
        session = ManagedCashService(a).open(1000, 'a')
        assert ManagedCashService(b).get_open().id == session.id
        with pytest.raises(ValueError, match='déjà ouverte'):
            ManagedCashService(b).open(500, 'b')
        assert b.query(ManagedCashSession).count() == 1
    finally:
        a.close(); b.close(); engine.dispose()
