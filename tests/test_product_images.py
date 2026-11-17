from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from services.product_service import ProductService
from services.product_image_service import ProductImageService


def test_image_locale_et_suppression_reference(db_session, tmp_path):
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille'})
    content = BytesIO()
    Image.new('RGB', (20, 20), 'red').save(content, format='JPEG')
    images = ProductImageService(db_session, tmp_path)
    saved = images.save(product.id, content.getvalue())
    assert images.safe_path(product) == saved
    assert Image.open(saved).format == 'PNG'
    images.remove(product.id)
    assert images.safe_path(product) is None
    assert saved.exists()  # préservation des anciens fichiers pour les sauvegardes
    product.image_path = '/etc/passwd'
    assert images.safe_path(product) is None


def test_image_refuse_fichier_invalide_et_trop_grand(db_session, tmp_path):
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille'})
    images = ProductImageService(db_session, tmp_path)
    for content in (b'', b'pas une image', b'0' * (5 * 1024 * 1024 + 1)):
        with pytest.raises(ValueError):
            images.save(product.id, content)
    assert product.image_path is None
    assert not list(tmp_path.iterdir())


def test_rollback_echec_bdd_ne_laissent_pas_fichier_orphelin(db_session, tmp_path, monkeypatch):
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille'})
    content = BytesIO()
    Image.new('RGB', (4, 4), 'blue').save(content, format='PNG')
    def fail():
        raise RuntimeError('échec simulé')
    monkeypatch.setattr(db_session, 'commit', fail)
    with pytest.raises(RuntimeError):
        ProductImageService(db_session, tmp_path).save(product.id, content.getvalue())
    assert list(tmp_path.iterdir()) == []
    assert db_session.get(type(product), product.id).image_path is None
