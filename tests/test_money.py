from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database import Base
import models  # charge tous les modèles avant la création des tables
from models.product import Category, Product
from money import fcfa
from validation import calculate_line_total, validate_amount


@pytest.mark.parametrize('value', [100, '100', Decimal('100.00'), 100.0, 0])
def test_fcfa_entier(value):
    assert fcfa(value) == int(value)
    assert isinstance(fcfa(value), int)


@pytest.mark.parametrize('value', ['0.5', Decimal('12.01'), float('nan'), float('inf'), True, None])
def test_fcfa_refuse_fraction_et_valeurs_invalides(value):
    with pytest.raises(ValueError):
        fcfa(value)


def test_quantites_decimales_sans_arrondi():
    assert calculate_line_total(Decimal('1.5'), 200) == 300
    with pytest.raises(ValueError):
        calculate_line_total(Decimal('1.5'), 201)
    with pytest.raises(ValueError):
        validate_amount('1.25')


def test_stockage_et_lecture_entiers():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    category = Category(name='Boissons')
    session.add(category)
    session.flush()
    product = Product(reference='P1', name='Eau', category_id=category.id, retail_price=125)
    session.add(product)
    session.commit()
    session.expire_all()
    assert type(session.get(Product, product.id).retail_price) is int
    assert session.execute(text('select typeof(retail_price) from products')).scalar() == 'integer'
    product.retail_price = Decimal('1.5')
    with pytest.raises(Exception, match='entier de FCFA'):
        session.commit()
    session.rollback()
    session.close()
    engine.dispose()


def test_vente_fractionnaire_ne_modifie_pas_le_stock(db_session):
    from services.sales_service import SalesService
    category = Category(name='Test vente')
    db_session.add(category)
    db_session.flush()
    product = Product(reference='TEST', name='Boisson', category_id=category.id,
                      stock_quantity=10, retail_price=201)
    db_session.add(product)
    db_session.commit()
    with pytest.raises(ValueError, match='entier de FCFA'):
        SalesService(db_session).create_sale({}, [
            {'product_id': product.id, 'quantity': Decimal('1.5'), 'unit_price': 201},
        ])
    assert db_session.get(Product, product.id).stock_quantity == 10


def test_stock_insuffisant_annule_toute_la_vente(db_session):
    from services.sales_service import SalesService
    from models.sale import Sale
    category = Category(name='Test stock')
    db_session.add(category)
    db_session.flush()
    first = Product(reference='A', name='A', category_id=category.id, stock_quantity=10)
    second = Product(reference='B', name='B', category_id=category.id, stock_quantity=1)
    db_session.add_all([first, second])
    db_session.commit()
    assert SalesService(db_session).create_sale({}, [
        {'product_id': first.id, 'quantity': 2, 'unit_price': 100},
        {'product_id': second.id, 'quantity': 2, 'unit_price': 100},
    ]) is None
    assert db_session.get(Product, first.id).stock_quantity == 10
    assert db_session.query(Sale).count() == 0


def test_audit_ancienne_base_sans_modification(tmp_path):
    import sqlite3
    from scripts.audit_fcfa import audit
    path = tmp_path / 'ancien.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE products (retail_price NUMERIC)')
        db.execute('INSERT INTO products VALUES (12.5)')
    assert audit(path) == [('products', 1, 'retail_price', 12.5)]
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT retail_price FROM products').fetchone()[0] == 12.5
