import pytest
from sqlalchemy import event
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedCashTransaction
from models.stock import StockMovement
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.product_service import ProductService
from services.packaging_service import PackagingService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'unit': 'bouteille', 'category_id': category.id, 'stock_quantity': 48})
    packaging = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000, 'wholesale_price': 2400})
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    return product, packaging, cash, session


def test_vente_comptant_et_flux_distincts(db_session, scenario):
    product, packaging, cash, session = scenario
    sale_service = ManagedSaleService(db_session)
    args = dict(session_id=session.id, mode='wholesale', method='cash', lines=[{'packaging_id': packaging.id, 'quantity': 1}], request_key='sale')
    sale = sale_service.sell(**args)
    assert sale_service.sell(**args).id == sale.id
    assert sale.total == 2400 and product.stock_quantity == 24
    assert db_session.query(StockMovement).filter_by(reference_document=sale.reference).one().quantity == -24
    assert db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).count() == 1
    assert cash.cash_available(session) == 3400
    cash.record(session.id, 'expense', 'cash', 600, 'Carburant tricycle', 'exp', category='Carburant')
    cash.record(session.id, 'income', 'wave', 200, 'Recette diverse', 'income')
    assert cash.cash_available(session) == 2800
    assert cash.flows(session.id) == {'cash': {'in': 2400, 'out': 600}, 'wave': {'in': 200, 'out': 0}}
    cash.close(session.id, 2800, '', 'close')
    assert session.theoretical_cash == 2800 and session.difference == 0


def test_vente_rollback_si_caisse_echoue(db_session, scenario):
    product, packaging, _, session = scenario
    def fail(_mapper, _connection, target):
        if target.kind == 'sale':
            raise RuntimeError('erreur de caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='erreur'):
            ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': packaging.id, 'quantity': 1}], 's1')
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 48
    assert db_session.query(ManagedSale).count() == db_session.query(ManagedSaleLine).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 0
    assert db_session.query(StockMovement).filter_by(movement_type='sale').count() == 0


def test_ventes_et_depenses_invalides(db_session, scenario):
    product, pack, cash, session = scenario
    sell = ManagedSaleService(db_session)
    with pytest.raises(ValueError, match='Stock insuffisant'):
        sell.sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 3}], 'trop')
    with pytest.raises(ValueError, match='Tarif non configuré'):
        sell.sell(session.id, 'semi_wholesale', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'tarif')
    with pytest.raises(ValueError, match='catégorie'):
        cash.record(session.id, 'expense', 'cash', 10, 'test', 'x')
    with pytest.raises(ValueError, match='insuffisantes'):
        cash.record(session.id, 'expense', 'cash', 1001, 'test', 'y', category='Test')
    with pytest.raises(ValueError, match='entier'):
        cash.record(session.id, 'income', 'cash', '1.5', 'test', 'z')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000


def test_mouvement_idempotent_et_cloture(db_session, scenario):
    _, _, cash, session = scenario
    entry = cash.record(session.id, 'expense', 'cash', 200, 'Transport', 'cle', category='Transport')
    assert cash.record(session.id, 'expense', 'cash', 200, 'Transport', 'cle', category='Transport').id == entry.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        cash.record(session.id, 'expense', 'cash', 300, 'Transport', 'cle', category='Transport')
    cash.close(session.id, 800, '', 'close')
    with pytest.raises(ValueError, match='ouverte'):
        cash.record(session.id, 'income', 'cash', 100, 'Autre', 'nouveau')
    assert db_session.query(ManagedCashTransaction).count() == 1


def test_prix_modifie_depuis_apercu_refuse_et_rollback(db_session, scenario):
    product, pack, cash, session = scenario
    lines = [{'packaging_id': pack.id, 'quantity': 1, 'expected_unit_price': 2000}]
    with pytest.raises(ValueError, match='tarif a changé'):
        ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', lines, 'prix')
    assert product.stock_quantity == 48
    assert cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0


def test_vente_produit_a_consigne_non_prise_en_charge_refusee(db_session, scenario):
    product, pack, cash, session = scenario
    product.consignment_value = 100
    db_session.commit()
    with pytest.raises(ValueError, match='consigne'):
        ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'consigne')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
