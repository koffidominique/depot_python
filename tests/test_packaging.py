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


def test_code_barres_ecritures_concurrentes_produit_conditionnement(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from database import Base
    from models.product import Product
    from models.packaging import ProductPackaging
    engine = create_engine(f'sqlite:///{tmp_path / "concurrent.db"}', connect_args={'timeout': 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    with factory() as db:
        products = ProductService(db)
        category = products.create_category('Test')
        product = products.create_product({'name': 'Initial', 'unit': 'bouteille', 'category_id': category.id})
        product_id, category_id = product.id, category.id
    barrier = Barrier(2)
    def write(kind):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                if kind == 'produit':
                    ProductService(db).create_product({'name': 'Autre', 'unit': 'bouteille',
                                                       'category_id': category_id, 'barcode': '123456'})
                else:
                    PackagingService(db).save(product_id, {'name': 'pack', 'coefficient': 6, 'barcode': '123456'})
                return True
            except ValueError as exc:
                assert 'code-barres' in str(exc)
                return False
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(write, ('produit', 'conditionnement'))) == [False, True]
        with factory() as db:
            product_count = len(db.execute(select(Product).where(Product.barcode == '123456')).scalars().all())
            package_count = len(db.execute(select(ProductPackaging).where(ProductPackaging.barcode == '123456')).scalars().all())
            assert product_count + package_count == 1
    finally:
        engine.dispose()


def test_refus_modifications_en_attente_ne_les_annule_pas(db_session, product):
    product.name = 'Modification non enregistrée'
    with pytest.raises(ValueError, match='modifications en cours'):
        PackagingService(db_session).save(product.id, {'name': 'pack', 'coefficient': 6})
    assert product.name == 'Modification non enregistrée'
    assert product in db_session.dirty
    db_session.rollback()


def test_conditionnement_canette_unite_de_base(db_session):
    products = ProductService(db_session)
    category = products.create_category('Canettes test')
    product = products.create_product({'name': 'Produit test canette', 'category_id': category.id,
                                       'unit': 'canette'})
    service = PackagingService(db_session)
    item = service.save(product.id, {'name': 'canette', 'coefficient': 1, 'retail_price': 250})
    assert service.to_base(item.id, 3) == Decimal('3')
    assert service.price(item.id, 'retail') == 250
    with pytest.raises(ValueError, match='coefficient de 1'):
        service.save(product.id, {'name': 'canette', 'coefficient': 2}, item.id)
