"""Conditionnements propres au produit ; aucun coefficient n'est prédéfini."""
from decimal import Decimal, InvalidOperation
from sqlalchemy import func
from models.product import Product
from models.packaging import ProductPackaging
from money import fcfa

PACKAGING_TYPES = ('casier', 'carton', 'bouteille', 'pack', 'canette')
PRICE_FIELDS = ('purchase_price', 'wholesale_price', 'retail_price', 'semi_wholesale_price')


def quantity(value, field='Quantité', allow_zero=False):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
            raise ValueError
        if number != number.quantize(Decimal('0.001')) or number >= Decimal('10000000'):
            raise ValueError
        return number
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'{field} doit être un nombre valide à 3 décimales maximum.') from None


class PackagingService:
    def __init__(self, db):
        self.db = db

    def list_for_product(self, product_id, include_inactive=False):
        query = self.db.query(ProductPackaging).filter_by(product_id=product_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(ProductPackaging.name).all()

    def save(self, product_id, data, packaging_id=None):
        product = self.db.get(Product, product_id)
        if not product or not product.is_active:
            raise ValueError('Produit actif introuvable.')
        name = str(data.get('name', '')).strip().lower()
        if name not in PACKAGING_TYPES:
            raise ValueError('Conditionnement inconnu.')
        coefficient = quantity(data.get('coefficient'), 'Coefficient')
        if not product.unit or product.unit == 'unit':
            raise ValueError('Définissez une unité de base explicite pour ce produit.')
        if name == product.unit.lower() and coefficient != 1:
            raise ValueError('Le conditionnement de base doit avoir un coefficient de 1.')
        duplicate = self.db.query(ProductPackaging).filter(
            ProductPackaging.product_id == product_id, func.lower(ProductPackaging.name) == name)
        if packaging_id is not None:
            duplicate = duplicate.filter(ProductPackaging.id != packaging_id)
        if duplicate.first():
            raise ValueError('Ce conditionnement existe déjà pour ce produit.')
        barcode = (data.get('barcode') or '').strip() or None
        if barcode:
            match = self.db.query(ProductPackaging).filter(ProductPackaging.barcode == barcode)
            if packaging_id is not None:
                match = match.filter(ProductPackaging.id != packaging_id)
            if match.first() or self.db.query(Product).filter(Product.barcode == barcode).first():
                raise ValueError('Ce code-barres est déjà utilisé.')
        prices = {}
        for field in PRICE_FIELDS:
            value = data.get(field)
            prices[field] = None if value in (None, '') else fcfa(value, field)
            if prices[field] is not None and prices[field] < 0:
                raise ValueError('Un prix ne peut pas être négatif.')
        item = self.db.get(ProductPackaging, packaging_id) if packaging_id is not None else None
        if packaging_id is not None and (not item or item.product_id != product_id):
            raise ValueError('Conditionnement introuvable.')
        if item is None:
            item = ProductPackaging(product_id=product_id)
            self.db.add(item)
        item.name = name
        item.base_unit = product.unit
        item.coefficient = coefficient
        item.barcode = barcode
        item.allow_fraction = bool(data.get('allow_fraction', False))
        item.is_active = bool(data.get('is_active', True))
        for field, value in prices.items():
            setattr(item, field, value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise

    def to_base(self, packaging_id, count):
        item = self.db.get(ProductPackaging, packaging_id)
        if not item or not item.is_active or not item.product.is_active:
            raise ValueError('Conditionnement actif introuvable.')
        count = quantity(count)
        if not item.allow_fraction and count != count.to_integral_value():
            raise ValueError('Ce conditionnement ne peut être vendu ou acheté en fraction.')
        return quantity(count * item.coefficient, 'Quantité convertie')

    def price(self, packaging_id, mode):
        if mode not in ('wholesale', 'retail', 'semi_wholesale'):
            raise ValueError('Tarif inconnu.')
        item = self.db.get(ProductPackaging, packaging_id)
        if not item or not item.is_active or not item.product.is_active:
            raise ValueError('Conditionnement actif introuvable.')
        result = getattr(item, mode + '_price')
        if result is None:
            raise ValueError('Ce tarif n’a pas été configuré.')
        return result
