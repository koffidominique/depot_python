from sqlalchemy.orm import Session
from services.product_service import ProductService

def test_create_and_search_product(db_session):
    product_service = ProductService(db_session)
    category = product_service.create_category(name="Electronics", description="Electronic devices")
    assert category.name == "Electronics"
    product = product_service.create_product({
        "unit": "bouteille",
        "name": "Smartphone",
        "purchase_price": 300.0,
        "retail_price": 500.0,
        "stock_quantity": 10,
        "min_stock": 2,
        "category_id": category.id
    })
    assert product is not None
    assert product.name == "Smartphone"
    assert product.reference is not None
    assert product.stock_quantity == 10
    assert product.is_active == True
    found_product = product_service.get_product_by_reference(product.reference)
    assert found_product is not None
    products = product_service.get_all_products()
    smartphone_products = [p for p in products if p.name == "Smartphone"]
    assert len(products) >= 1

def test_product_stock_calculations(db_session):
    product_service = ProductService(db_session)
    category = product_service.create_category(name="Informatique")
    product = product_service.create_product({
        "unit": "bouteille",
        "category_id": category.id,
        "name": "Laptop",
        "purchase_price": 800.0,
        "retail_price": 1200.0,
        "stock_quantity": 5,
        "min_stock": 1
    })
    assert product.stock_quantity == 5
    assert product.min_stock == 1
    assert product.stock_quantity > product.min_stock
    result = product_service.deactivate_product(product.id)
    assert result == True
    deactivated = product_service.get_product_by_id(product.id)
    assert deactivated.is_active == False


def test_pagination_et_recherche_sql(db_session):
    service = ProductService(db_session)
    category = service.create_category('Pagination')
    for i in range(31):
        service.create_product({'name': f'Produit {i:02}', 'category_id': category.id, 'unit': 'bouteille'})
    page1, total, current = service.get_products_page(page=1, page_size=10)
    page2, _, _ = service.get_products_page(page=2, page_size=10)
    assert total == 31 and current == 1 and len(page1) == len(page2) == 10
    assert not {p.id for p in page1} & {p.id for p in page2}
    result, total, _ = service.get_products_page(search='produit 01')
    assert total == 1 and result[0].name == 'Produit 01'
    assert service.get_products_page(search='%')[1] == 0
    assert service.get_products_page(page=999, page_size=10)[2] == 4


def test_declaration_unite_legacy_tracee(db_session):
    import pytest
    from models.stock import StockMovement
    service = ProductService(db_session)
    category = service.create_category('Ancien')
    product = service.create_product({'name': 'Ancien produit', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 9})
    # Simulation d'une installation historique dont l'unité n'était pas précisée.
    product.unit = 'unit'
    product.stock_movements[0].unit = 'unit'
    db_session.commit()
    with pytest.raises(ValueError, match='confirmation'):
        service.declare_legacy_base_unit(product.id, 'bouteille', 'Vérification des archives')
    with pytest.raises(ValueError, match='motif'):
        service.declare_legacy_base_unit(product.id, 'bouteille', 'x', confirmed=True)
    service.declare_legacy_base_unit(product.id, 'bouteille', 'Vérification des archives', confirmed=True)
    assert product.unit == 'bouteille' and product.stock_quantity == 9
    movement = db_session.query(StockMovement).filter_by(movement_type='unit_declaration').one()
    assert movement.quantity == 0 and movement.stock_before == movement.stock_after == 9
    assert movement.reason == 'Vérification des archives'
    with pytest.raises(ValueError, match='historique générique'):
        service.declare_legacy_base_unit(product.id, 'canette', 'Vérification des archives', confirmed=True)


def test_cout_moyen_exact_sans_estimation(db_session):
    from fractions import Fraction
    service = ProductService(db_session)
    category = service.create_category('Coûts')
    product = service.create_product({'name': 'Test coût', 'category_id': category.id, 'unit': 'bouteille'})
    assert product.average_cost is None
    product.average_cost_numerator = '1001'
    product.average_cost_denominator = '6'
    db_session.commit()
    db_session.expire_all()
    assert service.get_product_by_id(product.id).average_cost == Fraction(1001, 6)


def test_prix_non_renseignes_ne_sont_pas_inventes(db_session):
    import pytest
    from services.stock_service import StockService
    service = ProductService(db_session)
    category = service.create_category('Sans prix')
    product = service.create_product({'name': 'Article', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 5})
    assert product.purchase_price is None and product.retail_price is None
    with pytest.raises(ValueError, match='valorisation indisponible'):
        StockService(db_session).get_total_stock_value()


def test_creation_refuse_unite_generique(db_session):
    import pytest
    service = ProductService(db_session)
    category = service.create_category('Sans unité')
    for unit in (None, '', 'unit'):
        with pytest.raises(ValueError, match='unité'):
            service.create_product({'name': 'Test', 'category_id': category.id, 'unit': unit})


def test_champ_prix_vide_reste_inconnu(db_session):
    service = ProductService(db_session)
    category = service.create_category('Test')
    product = service.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille',
                                      'purchase_price': '', 'retail_price': ''})
    assert product.purchase_price is None and product.retail_price is None


def test_valorisation_exige_cout_moyen_et_refuse_fraction(db_session):
    import pytest
    from services.stock_service import StockService
    service = ProductService(db_session)
    category = service.create_category('Stock')
    product = service.create_product({'name': 'Article', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 3, 'purchase_price': 999})
    with pytest.raises(ValueError, match='Coût moyen'):
        StockService(db_session).get_total_stock_value()
    product.average_cost_numerator = '1'
    product.average_cost_denominator = '2'
    db_session.commit()
    with pytest.raises(ValueError, match='nombre entier'):
        StockService(db_session).get_total_stock_value()
    product.average_cost_numerator = '200'
    product.average_cost_denominator = '1'
    db_session.commit()
    assert StockService(db_session).get_total_stock_value() == 600
