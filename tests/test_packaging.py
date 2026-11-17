from decimal import Decimal
import pytest
from models.stock import StockMovement
from services.product_service import ProductService
from services.packaging_service import PackagingService


@pytest.fixture
def product(db_session):
    service = ProductService(db_session)
    category = service.create_category('Boissons')
    return service.create_product({'name': 'Produit test', 'unit': 'bouteille',
                                   'category_id': category.id, 'stock_quantity': 10})


def test_coefficient_et_tarifs_par_produit(db_session, product):
    service = PackagingService(db_session)
    for name, coefficient in [('pack', 6), ('carton', 12), ('casier', 24), ('bouteille', 1)]:
        item = service.save(product.id, {'name': name, 'coefficient': coefficient,
                                        'wholesale_price': 12000, 'retail_price': 15000})
        assert service.to_base(item.id, 2) == Decimal(2 * coefficient)
        assert service.price(item.id, 'wholesale') == 12000
        assert service.price(item.id, 'retail') == 15000
        with pytest.raises(ValueError, match='configuré'):
            service.price(item.id, 'semi_wholesale')


def test_parametres_invalides_et_fraction(db_session, product):
    service = PackagingService(db_session)
    for coeff in [0, -1, 'NaN', '0.0001']:
        with pytest.raises(ValueError):
            service.save(product.id, {'name': 'pack', 'coefficient': coeff})
    with pytest.raises(ValueError, match='coefficient de 1'):
        service.save(product.id, {'name': 'bouteille', 'coefficient': 6})
    with pytest.raises(ValueError):
        service.save(product.id, {'name': 'pack', 'coefficient': 6, 'retail_price': '1.5'})
    item = service.save(product.id, {'name': 'pack', 'coefficient': 6})
    with pytest.raises(ValueError, match='fraction'):
        service.to_base(item.id, '0.5')
    with pytest.raises(ValueError, match='existe déjà'):
        service.save(product.id, {'name': 'PACK', 'coefficient': 12})
    service.save(product.id, {'name': 'pack', 'coefficient': 6, 'allow_fraction': True}, item.id)
    assert service.to_base(item.id, '0.5') == Decimal('3.000')


def test_stock_initial_trace_et_modification_directe_interdite(db_session, product):
    movements = db_session.query(StockMovement).filter_by(product_id=product.id).all()
    assert len(movements) == 1
    assert movements[0].movement_type == 'initial_stock'
    assert (movements[0].stock_before, movements[0].stock_after) == (0, 10)
    with pytest.raises(ValueError, match='non modifiables'):
        ProductService(db_session).update_product(product.id, {'stock_quantity': 999})
    with pytest.raises(ValueError, match='unité de base'):
        ProductService(db_session).update_product(product.id, {'unit': 'canette'})
    assert product.stock_quantity == 10


def test_archive_produit_sans_suppression(db_session, product):
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24})
    ProductService(db_session).deactivate_product(product.id)
    with pytest.raises(ValueError, match='actif'):
        PackagingService(db_session).to_base(pack.id, 1)
    assert db_session.get(type(product), product.id) is not None


def test_tarif_intermediaire_produit_facultatif(db_session, product):
    service = ProductService(db_session)
    service.update_product(product.id, {'semi_wholesale_price': ''})
    assert product.semi_wholesale_price is None


def test_codes_barres_uniques_entre_produits_et_conditionnements(db_session, product):
    service = PackagingService(db_session)
    service.save(product.id, {'name': 'carton', 'coefficient': 12, 'barcode': '123'})
    with pytest.raises(ValueError, match='code-barres'):
        ProductService(db_session).update_product(product.id, {'barcode': '123'})
    ProductService(db_session).update_product(product.id, {'barcode': '456'})
    with pytest.raises(ValueError, match='code-barres'):
        service.save(product.id, {'name': 'pack', 'coefficient': 6, 'barcode': '456'})
