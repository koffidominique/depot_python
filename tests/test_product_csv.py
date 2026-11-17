import csv
import io
import pytest
from models.product import Product
from models.stock import StockMovement
from services.product_csv_service import FIELDS, ProductCSVService
from services.product_service import ProductService


def csv_content(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def row(**overrides):
    return dict({'reference': 'P001', 'name': 'Eau', 'category': 'Boissons', 'unit': 'bouteille',
                 'barcode': '', 'purchase_price': '100', 'wholesale_price': '120',
                 'retail_price': '150', 'semi_wholesale_price': '130', 'stock_quantity': '12',
                 'min_stock': '2'}, **overrides)


def test_csv_previsualisation_import_et_export(db_session):
    ProductService(db_session).create_category('Boissons')
    service = ProductCSVService(db_session)
    text = csv_content([row()])
    assert not service.preview(text)[0]['errors']
    assert service.import_csv(text) == 1
    assert db_session.query(Product).count() == 1
    assert db_session.query(StockMovement).one().quantity == 12
    exported = list(csv.DictReader(io.StringIO(service.export_csv())))
    assert exported[0]['reference'] == 'P001'
    assert service.preview(text)[0]['errors']


def test_csv_refus_atomique_ligne_invalide(db_session):
    ProductService(db_session).create_category('Boissons')
    service = ProductCSVService(db_session)
    text = csv_content([row(), row(reference='P002', retail_price='4.5')])
    assert service.preview(text)[1]['errors']
    with pytest.raises(ValueError, match='Import annulé'):
        service.import_csv(text)
    assert db_session.query(Product).count() == 0
    assert db_session.query(StockMovement).count() == 0


def test_csv_refuse_doublons_dans_fichier(db_session):
    ProductService(db_session).create_category('Boissons')
    service = ProductCSVService(db_session)
    assert service.preview(csv_content([row(), row(name='Autre')]))[1]['errors']
