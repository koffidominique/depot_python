from sqlalchemy.orm import Session
from services.product_service import ProductService

def test_create_and_search_product(db_session):
    product_service = ProductService(db_session)
    category = product_service.create_category(name="Electronics", description="Electronic devices")
    assert category.name == "Electronics"
    product = product_service.create_product({
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
    smartphone_products = [p for p in products if p.name == "Smartphone"]
    assert len(products) >= 1

def test_product_stock_calculations(db_session):
    product_service = ProductService(db_session)
    product = product_service.create_product({
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
