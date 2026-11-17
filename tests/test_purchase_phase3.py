from fractions import Fraction
from decimal import Decimal
import pytest
from models.supplier import Supplier
from models.stock import StockMovement
from models.reception import PurchaseReceipt
from services.product_service import ProductService
from services.packaging_service import PackagingService
from services.purchase_service import PurchaseService


@pytest.fixture
def setup_order(db_session):
    supplier = Supplier(code='F1', name='Fournisseur', phone='0101')
    db_session.add(supplier)
    db_session.commit()
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Produit', 'unit': 'bouteille', 'category_id': category.id, 'stock_quantity': 0})
    packaging = PackagingService(db_session).save(product.id, {'name': 'pack', 'coefficient': 6})
    service = PurchaseService(db_session)
    order = service.create_purchase_order({'supplier_id': supplier.id}, [{'packaging_id': packaging.id, 'ordered_quantity': 3, 'unit_price': 1000}])
    return service, order, product, packaging


def test_reception_partielle_idempotente_et_conversion_figee(db_session, setup_order):
    service, order, product, packaging = setup_order
    line_id = order.purchase_order_lines[0].id
    service.validate_purchase_order(order.id)
    PackagingService(db_session).save(product.id, {'name': 'pack', 'coefficient': 12}, packaging.id)
    data = [{'line_id': line_id, 'received_quantity': 1}]
    first = service.receive_purchase_order(order.id, data, request_key='unique-1')
    assert product.stock_quantity == 6
    assert product.average_cost == Fraction(500, 3)
    assert order.status == 'partially_received'
    assert service.receive_purchase_order(order.id, data, request_key='unique-1').id == first.id
    assert product.stock_quantity == 6
    with pytest.raises(ValueError, match='déjà été utilisée'):
        service.receive_purchase_order(order.id, [{'line_id': line_id, 'received_quantity': 2}], request_key='unique-1')
    with pytest.raises(ValueError, match='dépasse'):
        service.receive_purchase_order(order.id, [{'line_id': line_id, 'received_quantity': 3}], request_key='unique-2')
    assert db_session.query(PurchaseReceipt).count() == 1
    service.receive_purchase_order(order.id, [{'line_id': line_id, 'received_quantity': 2}], request_key='unique-3')
    assert product.stock_quantity == 18
    assert order.received_amount == 3000
    assert order.status == 'received'
    assert db_session.query(StockMovement).filter_by(movement_type='purchase_reception').count() == 2


def test_fraction_fcfa_reception_rollback(db_session, setup_order):
    service, order, product, packaging = setup_order
    # Une commande à quantité entière et prix entier, mais réception fractionnaire.
    line = order.purchase_order_lines[0]
    line.allow_fraction = True
    line.unit_price = 1
    db_session.commit()
    service.validate_purchase_order(order.id)
    with pytest.raises(ValueError, match='entier'):
        service.receive_purchase_order(order.id, [{'line_id': line.id, 'received_quantity': Decimal('0.5')}], request_key='unique')
    assert product.stock_quantity == 0
    assert db_session.query(PurchaseReceipt).count() == 0


def test_dix_casiers_de_24_et_cout_moyen_pondere(db_session):
    supplier = Supplier(code='F2', name='Fournisseur', phone='01')
    db_session.add(supplier)
    db_session.commit()
    product_service = ProductService(db_session)
    category = product_service.create_category('Boissons B')
    product = product_service.create_product({'name': 'Boisson', 'unit': 'bouteille', 'category_id': category.id, 'stock_quantity': 0})
    case = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24})
    service = PurchaseService(db_session)
    order = service.create_purchase_order({'supplier_id': supplier.id}, [{'packaging_id': case.id, 'ordered_quantity': 10, 'unit_price': 2400}])
    assert product.stock_quantity == 0
    service.validate_purchase_order(order.id)
    assert product.stock_quantity == 0
    service.receive_purchase_order(order.id, [{'line_id': order.purchase_order_lines[0].id, 'received_quantity': 10}], request_key='casier-10')
    assert product.stock_quantity == 240
    assert product.average_cost == Fraction(100)
    second = service.create_purchase_order({'supplier_id': supplier.id}, [{'packaging_id': case.id, 'ordered_quantity': 10, 'unit_price': 4800}])
    service.validate_purchase_order(second.id)
    service.receive_purchase_order(second.id, [{'line_id': second.purchase_order_lines[0].id, 'received_quantity': 10}], request_key='casier-20')
    assert product.stock_quantity == 480
    assert product.average_cost == Fraction(150)


def test_stock_initial_sans_cout_ne_fabrique_pas_de_valorisation(db_session):
    supplier = Supplier(code='F3', name='Fournisseur', phone='01')
    db_session.add(supplier)
    db_session.commit()
    products = ProductService(db_session)
    category = products.create_category('Test inconnu')
    product = products.create_product({'name': 'Produit inconnu', 'unit': 'bouteille', 'category_id': category.id, 'stock_quantity': 2})
    pack = PackagingService(db_session).save(product.id, {'name': 'pack', 'coefficient': 6})
    service = PurchaseService(db_session)
    order = service.create_purchase_order({'supplier_id': supplier.id}, [{'packaging_id': pack.id, 'ordered_quantity': 1, 'unit_price': 600}])
    service.validate_purchase_order(order.id)
    service.receive_purchase_order(order.id, [{'line_id': order.purchase_order_lines[0].id, 'received_quantity': 1}], request_key='inconnu')
    assert product.stock_quantity == 8
    assert product.average_cost is None


def test_reception_plusieurs_lignes_annulation_complete(db_session, setup_order):
    service, order, product, packaging = setup_order
    # Une deuxième ligne invalide doit annuler aussi la première ligne traitée.
    line_id = order.purchase_order_lines[0].id
    service.validate_purchase_order(order.id)
    with pytest.raises(ValueError, match='introuvable'):
        service.receive_purchase_order(order.id, [{'line_id': line_id, 'received_quantity': 1},
                                                   {'line_id': 999999, 'received_quantity': 1}], request_key='rollback')
    assert product.stock_quantity == 0
    assert order.received_amount == 0
    assert db_session.query(PurchaseReceipt).count() == 0
    assert db_session.query(StockMovement).filter_by(movement_type='purchase_reception').count() == 0


def test_remises_frais_et_paiements_fournisseurs(db_session, setup_order):
    from models.debt import SupplierDebt
    from models.payment import Payment
    from services.purchase_service import SupplierPaymentService
    service, _, product, pack = setup_order
    supplier = db_session.query(Supplier).one()
    order = service.create_purchase_order({'supplier_id': supplier.id, 'reference': 'CMD-EXEMPLE'}, [
        {'packaging_id': pack.id, 'ordered_quantity': 3, 'unit_price': 1000, 'unit_discount': 100, 'unit_fee': 50}])
    assert order.total_amount == 2850
    service.validate_purchase_order(order.id)
    receipt = service.receive_purchase_order(order.id, [{'line_id': order.purchase_order_lines[0].id, 'received_quantity': 2}], request_key='rec-remise')
    debt = db_session.query(SupplierDebt).filter_by(receipt_id=receipt.id).one()
    assert (receipt.total_amount, debt.initial_amount, supplier.balance_due, supplier.total_purchases) == (1900, 1900, 1900, 1900)
    assert product.average_cost == Fraction(950, 6)
    payments = SupplierPaymentService(db_session)
    from services.managed_cash_service import ManagedCashService
    caisse = ManagedCashService(db_session).open(1000, 'open-1')
    paid = payments.pay(debt.id, 700, 'cash', 'reglement-1', cash_session_id=caisse.id)
    assert paid.cash_link_status == 'linked_cash'
    assert payments.pay(debt.id, 700, 'cash', 'reglement-1', cash_session_id=caisse.id).id == paid.id
    assert (debt.paid_amount, debt.remaining_amount, supplier.balance_due) == (700, 1200, 1200)
    with pytest.raises(ValueError, match='déjà été utilisée'):
        payments.pay(debt.id, 701, 'cash', 'reglement-1', cash_session_id=caisse.id)
    with pytest.raises(ValueError, match='dépasse'):
        payments.pay(debt.id, 1201, 'transfer', 'reglement-2', cash_session_id=caisse.id)
    with pytest.raises(ValueError, match='entier'):
        payments.pay(debt.id, '0.5', 'cash', 'reglement-3', cash_session_id=caisse.id)
    assert db_session.query(Payment).filter_by(supplier_debt_id=debt.id).count() == 1
    payments.pay(debt.id, 1200, 'mobile_money', 'reglement-4', cash_session_id=caisse.id)
    assert debt.status == 'paid' and debt.remaining_amount == supplier.balance_due == 0


def test_remise_superieure_au_prix_refusee(db_session, setup_order):
    service, _, _, pack = setup_order
    supplier = db_session.query(Supplier).one()
    with pytest.raises(ValueError, match='remise'):
        service.create_purchase_order({'supplier_id': supplier.id}, [
            {'packaging_id': pack.id, 'ordered_quantity': 1, 'unit_price': 100, 'unit_discount': 101}])


def test_echeance_et_reprise_idempotente(db_session, setup_order):
    from models.debt import SupplierDebt
    service, order, _, _ = setup_order
    service.validate_purchase_order(order.id)
    data = [{'line_id': order.purchase_order_lines[0].id, 'received_quantity': 1}]
    receipt = service.receive_purchase_order(order.id, data, request_key='echeance', due_date='2030-01-15')
    assert db_session.query(SupplierDebt).filter_by(receipt_id=receipt.id).one().due_date.isoformat().startswith('2030-01-15')
    assert service.receive_purchase_order(order.id, data, request_key='echeance', due_date='2030-01-15').id == receipt.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        service.receive_purchase_order(order.id, data, request_key='echeance', due_date='2030-01-16')
