import pytest
from decimal import Decimal
from services.stock_service import StockService
from services.product_service import ProductService

def test_update_stock_product_exists(db_session):
    product_service = ProductService(db_session)
    stock_service = StockService(db_session)
    
    category = product_service.create_category(name="Test Category", description="Test")
    product = product_service.create_product({
        "name": "Test Product",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('10.0'),
        "category_id": category.id
    })
    
    initial_stock = product.stock_quantity
    result = stock_service.update_stock(
        product_id=product.id,
        quantity_change=Decimal('5.0'),
        movement_type="entry",
        unit="unit",
        reason="Test entry",
        commit=True
    )
    
    assert result is True
    db_session.refresh(product)
    assert product.stock_quantity == initial_stock + Decimal('5.0')

def test_update_stock_product_not_exists(db_session):
    stock_service = StockService(db_session)
    
    result = stock_service.update_stock(
        product_id=99999,
        quantity_change=Decimal('5.0'),
        movement_type="entry"
    )
    
    assert result is False

def test_negative_stock_forbidden_by_default(db_session):
    product_service = ProductService(db_session)
    stock_service = StockService(db_session)
    
    category = product_service.create_category(name="Test Category 2", description="Test")
    product = product_service.create_product({
        "name": "Test Product 2",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('5.0'),
        "category_id": category.id
    })
    
    result = stock_service.update_stock(
        product_id=product.id,
        quantity_change=Decimal('-10.0'),
        movement_type="exit",
        reason="Test negative stock"
    )
    
    assert result is False
    db_session.refresh(product)
    assert product.stock_quantity == Decimal('5.0')

def test_negative_stock_allowed_with_parameter(db_session):
    product_service = ProductService(db_session)
    stock_service = StockService(db_session)
    
    category = product_service.create_category(name="Test Category 3", description="Test")
    product = product_service.create_product({
        "name": "Test Product 3",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('5.0'),
        "category_id": category.id
    })
    
    result = stock_service.update_stock(
        product_id=product.id,
        quantity_change=Decimal('-10.0'),
        movement_type="exit",
        reason="Test negative stock allowed",
        allow_negative_stock=True
    )
    
    assert result is True
    db_session.refresh(product)
    assert product.stock_quantity == Decimal('-5.0')

def test_stock_movement_logs_before_after(db_session):
    product_service = ProductService(db_session)
    stock_service = StockService(db_session)
    
    category = product_service.create_category(name="Test Category 4", description="Test")
    product = product_service.create_product({
        "name": "Test Product 4",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('10.0'),
        "category_id": category.id
    })
    
    stock_service.update_stock(
        product_id=product.id,
        quantity_change=Decimal('3.0'),
        movement_type="entry",
        unit="unit",
        user_id=1,
        reason="Test movement log",
        reference_document="DOC-001",
        commit=True
    )
    
    movements = stock_service.get_stock_movements(product_id=product.id, limit=1)
    assert len(movements) == 1
    assert movements[0].stock_before == Decimal('10.0')
    assert movements[0].stock_after == Decimal('13.0')
    assert movements[0].unit == "unit"
    assert movements[0].user_id == 1
    assert movements[0].reason == "Test movement log"
    assert movements[0].reference_document == "DOC-001"

def test_no_commit_for_batch_operations(db_session):
    product_service = ProductService(db_session)
    stock_service = StockService(db_session)
    
    category = product_service.create_category(name="Test Category 5", description="Test")
    product = product_service.create_product({
        "name": "Test Product 5",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('10.0'),
        "category_id": category.id
    })
    
    result = stock_service.update_stock(
        product_id=product.id,
        quantity_change=Decimal('5.0'),
        movement_type="entry",
        commit=False
    )
    
    assert result is True
    db_session.refresh(product)
    assert product.stock_quantity == Decimal('15.0')
    
    db_session.rollback()
    db_session.refresh(product)
    assert product.stock_quantity == Decimal('10.0')