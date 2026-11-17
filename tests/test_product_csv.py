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


@pytest.mark.parametrize('text', [
    '"en-tête jamais terminé',
    ','.join(FIELDS) + '\nP01,"nom jamais terminé',
])
def test_csv_malforme_refuse_sans_ecriture(db_session, text):
    service = ProductCSVService(db_session)
    with pytest.raises(ValueError, match='illisible'):
        service.import_csv(text)
    assert db_session.query(Product).count() == 0
    assert db_session.query(StockMovement).count() == 0


def test_csv_refuse_code_barres_conditionnement_et_preserve_donnees(db_session):
    from services.packaging_service import PackagingService
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    existing = products.create_product({'name': 'Existant', 'category_id': category.id,
                                        'unit': 'bouteille'})
    PackagingService(db_session).save(existing.id, {'name': 'pack', 'coefficient': 6,
                                                   'barcode': 'CODE-TEST'})
    service = ProductCSVService(db_session)
    text = csv_content([row(reference='P001', barcode='CODE-TEST')])
    assert service.preview(text)[0]['errors']
    with pytest.raises(ValueError, match='Import annulé'):
        service.import_csv(text)
    assert db_session.query(Product).count() == 1
    assert db_session.query(StockMovement).count() == 0
