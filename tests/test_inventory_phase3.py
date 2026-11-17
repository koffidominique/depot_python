import pytest
from models.stock import StockMovement
from services.inventory_service import InventoryService
from services.product_service import ProductService
from services.stock_service import StockService
from decimal import Decimal


@pytest.fixture
def products(db_session):
    service = ProductService(db_session)
    category = service.create_category('Test')
    return [service.create_product({'name': f'Produit {i}', 'unit': 'bouteille',
                                    'category_id': category.id, 'stock_quantity': 10}) for i in range(2)]


def test_inventaire_correction_tracee_et_double_validation(db_session, products):
    service = InventoryService(db_session)
    inventory = service.start([p.id for p in products])
    lines = inventory.lines
    service.save_counts(inventory.id, [{'line_id': lines[0].id, 'counted_quantity': 7, 'reason': 'Casse'},
                                       {'line_id': lines[1].id, 'counted_quantity': 10}])
    service.validate(inventory.id)
    assert products[0].stock_quantity == 7
    movement = db_session.query(StockMovement).filter_by(reference_document=inventory.reference).one()
    assert (movement.stock_before, movement.stock_after, movement.quantity, movement.reason) == (10, 7, -3, 'Casse')
    with pytest.raises(ValueError, match='brouillon'):
        service.validate(inventory.id)
    assert db_session.query(StockMovement).filter_by(reference_document=inventory.reference).count() == 1


def test_inventaire_rollback_et_stock_modifie(db_session, products):
    service = InventoryService(db_session)
    inventory = service.start([p.id for p in products])
    lines = inventory.lines
    service.save_counts(inventory.id, [{'line_id': lines[0].id, 'counted_quantity': 8, 'reason': 'Perte'},
                                       {'line_id': lines[1].id, 'counted_quantity': 9}])
    with pytest.raises(ValueError, match='motif'):
        service.validate(inventory.id)
    assert products[0].stock_quantity == 10
    assert db_session.query(StockMovement).filter_by(reference_document=inventory.reference).count() == 0
    service.save_counts(inventory.id, [{'line_id': lines[1].id, 'counted_quantity': 9, 'reason': 'Perte'}])
    assert StockService(db_session).update_stock(products[1].id, Decimal('-1'), 'loss', unit='bouteille')
    with pytest.raises(ValueError, match='stock a changé'):
        service.validate(inventory.id)
    assert products[0].stock_quantity == 10


def test_augmentation_inventaire_ne_fabrique_pas_de_cout(db_session, products):
    product = products[0]
    product.average_cost_numerator, product.average_cost_denominator = '100', '1'
    db_session.commit()
    service = InventoryService(db_session)
    inventory = service.start([product.id])
    service.save_counts(inventory.id, [{'line_id': inventory.lines[0].id, 'counted_quantity': 11, 'reason': 'Erreur de comptage'}])
    service.validate(inventory.id)
    assert product.stock_quantity == 11
    assert product.average_cost is None


def test_annule_si_mouvements_intermediaires_meme_stock(db_session, products):
    service = InventoryService(db_session)
    inventory = service.start([products[0].id])
    service.save_counts(inventory.id, [{'line_id': inventory.lines[0].id, 'counted_quantity': 10}])
    stock = StockService(db_session)
    stock.update_stock(products[0].id, Decimal('1'), 'entry', unit='bouteille')
    stock.update_stock(products[0].id, Decimal('-1'), 'exit', unit='bouteille')
    with pytest.raises(ValueError, match='stock a changé'):
        service.validate(inventory.id)


def test_correction_manuelle_et_cout(db_session, products):
    from services.stock_adjustment_service import StockAdjustmentService
    product = products[0]
    product.average_cost_numerator, product.average_cost_denominator = '100', '1'
    db_session.commit()
    service = StockAdjustmentService(db_session)
    with pytest.raises(ValueError, match='motif'):
        service.adjust(product.id, 'loss', 1, '')
    with pytest.raises(ValueError, match='négatif'):
        service.adjust(product.id, 'loss', 11, 'Perte')
    service.adjust(product.id, 'breakage', 2, 'Casse')
    assert product.stock_quantity == 8 and product.average_cost == 100
    service.adjust(product.id, 'correction_in', 1, 'Retrouvé')
    assert product.stock_quantity == 9 and product.average_cost is None
    assert db_session.query(StockMovement).filter_by(movement_type='breakage').one().reason == 'Casse'
