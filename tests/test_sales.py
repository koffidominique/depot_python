import pytest
from sqlalchemy.orm import Session
from services.product_service import ProductService
from services.sales_service import SalesService
from services.client_service import ClientService
from decimal import Decimal


def test_create_sale(db_session):
    product_service = ProductService(db_session)
    sales_service = SalesService(db_session)
    client_service = ClientService(db_session)
    
    category = product_service.create_category(name="Test Category", description="Test")
    product = product_service.create_product({
        "name": "Test Product",
        "purchase_price": Decimal('10.00'),
        "retail_price": Decimal('20.00'),
        "stock_quantity": Decimal('100.0'),
        "category_id": category.id
    })
    
    client = client_service.create_client({
        "name": "Test Client",
        "phone": "+22500000000",
        "email": "test@client.com"
    })
    
    sale_lines = [
        {
            "product_id": product.id,
            "quantity": Decimal('5.0'),
            "unit_price": Decimal('20.00')
        }
    ]
    
    sale = sales_service.create_sale(
        client_id=client.id,
        sale_lines=sale_lines,
        payment_method="cash"
    )
    
    assert sale is not None
    assert sale.reference is not None
    assert sale.total_amount == Decimal('100.00')
    assert sale.remaining_amount == Decimal('0.00')


def test_sale_validation(db_session):
    sales_service = SalesService(db_session)
    
    with pytest.raises(Exception):
        sales_service.create_sale(
            client_id=None,
            sale_lines=[],
            payment_method="cash"
        )