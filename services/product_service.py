from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from models.product import Product, Category
from typing import List, Optional
from uuid import uuid4
from decimal import Decimal
from models.stock import StockMovement
from models.packaging import ProductPackaging
from services.packaging_service import quantity
from money import fcfa

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_products(self, include_inactive: bool = False) -> List[Product]:
        query = self.db.query(Product)
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        return query.all()
    
    def get_products_page(self, *, page=1, page_size=15, search='', category_id=None, include_inactive=False):
        if not isinstance(page, int) or page < 1 or not isinstance(page_size, int) or not 1 <= page_size <= 100:
            raise ValueError('Pagination invalide.')
        query = self.db.query(Product)
        if not include_inactive:
            query = query.filter(Product.is_active.is_(True))
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        if search:
            # Échapper les caractères de recherche SQL, pas d'interprétation comme joker.
            term = search.strip().replace('!', '!!').replace('%', '!%').replace('_', '!_')
            pattern = f'%{term}%'
            query = query.filter(or_(Product.name.ilike(pattern, escape='!'),
                                     Product.reference.ilike(pattern, escape='!'),
                                     Product.barcode.ilike(pattern, escape='!')))
        total = query.count()
        last_page = max(1, (total + page_size - 1) // page_size)
        page = min(page, last_page)
        results = (query.options(joinedload(Product.category))
                   .order_by(func.lower(Product.name), Product.id)
                   .offset((page - 1) * page_size).limit(page_size).all())
        return results, total, page

    def declare_legacy_base_unit(self, product_id, unit, reason, *, confirmed=False):
        """Déclare explicitement une unité historique générique sans convertir le stock."""
        if confirmed is not True:
            raise ValueError('Une confirmation explicite est obligatoire.')
        if not isinstance(reason, str) or len(reason.strip()) < 10:
            raise ValueError('Indiquez un motif précis (au moins 10 caractères).')
        normalized = self._validate_data({'unit': unit})['unit']
        if normalized == 'unit':
            raise ValueError('Renseignez l’unité réelle, différente de unit.')
        product = self.db.get(Product, product_id)
        if not product or product.unit != 'unit':
            raise ValueError('Seule une unité historique générique peut être précisée ici.')
        if product.packagings:
            raise ValueError('Des conditionnements existent déjà : intervention manuelle requise.')
        if any(m.unit not in (None, '', 'unit') for m in product.stock_movements):
            raise ValueError('L’historique contient des unités différentes : intervention manuelle requise.')
        before = product.stock_quantity
        product.unit = normalized
        self.db.add(StockMovement(product_id=product.id, movement_type='unit_declaration',
                                  quantity=Decimal('0'), unit=normalized,
                                  stock_before=before, stock_after=before,
                                  reason=reason.strip(), reference_document=product.reference))
        try:
            self.db.commit()
            return product
        except Exception:
            self.db.rollback()
            raise

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_reference(self, reference: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.reference == reference).first()
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    
    _FIELDS = {'name', 'barcode', 'brand', 'category_id', 'description', 'supplier_id',
               'unit', 'purchase_price', 'wholesale_price', 'semi_wholesale_price',
               'retail_price', 'min_stock', 'max_stock', 'consignment_value'}
    _PRICES = {'purchase_price', 'wholesale_price', 'semi_wholesale_price', 'retail_price', 'consignment_value'}

    def _validate_data(self, data):
        unknown = set(data) - self._FIELDS
        if unknown:
            raise ValueError(f'Champs non modifiables : {", ".join(sorted(unknown))}')
        data = dict(data)
        if 'name' in data:
            if not isinstance(data['name'], str) or not data['name'].strip():
                raise ValueError('Le nom du produit est obligatoire.')
            data['name'] = data['name'].strip()
        if 'category_id' in data and not self.db.get(Category, data['category_id']):
            raise ValueError('Catégorie introuvable.')
        if 'unit' in data:
            if not isinstance(data['unit'], str) or not data['unit'].strip():
                raise ValueError('L’unité de base est obligatoire.')
            data['unit'] = data['unit'].strip().lower()
        if 'barcode' in data:
            data['barcode'] = (data['barcode'] or '').strip() or None
            if data['barcode'] and self.db.query(ProductPackaging).filter_by(barcode=data['barcode']).first():
                raise ValueError('Ce code-barres est déjà utilisé par un conditionnement.')
        for field in self._PRICES & data.keys():
            if data[field] in (None, ''):
                data[field] = None
                continue
            data[field] = fcfa(data[field], field)
            if data[field] < 0:
                raise ValueError('Un prix ne peut pas être négatif.')
        for field in {'min_stock', 'max_stock'} & data.keys():
            data[field] = quantity(data[field], field, allow_zero=True)
        return data

    def create_product(self, product_data: dict) -> Product:
        data = dict(product_data)
        initial = quantity(data.pop('stock_quantity', 0), 'Stock initial', allow_zero=True)
        data = self._validate_data(data)
        if not data.get('name') or not data.get('category_id'):
            raise ValueError('Nom et catégorie sont obligatoires.')
        if not data.get('unit') or data['unit'] == 'unit':
            raise ValueError('L’unité de base réelle est obligatoire.')
        product = Product(reference=self._generate_reference(), stock_quantity=initial, **data)
        try:
            self.db.add(product)
            self.db.flush()
            if initial:
                self.db.add(StockMovement(product_id=product.id, movement_type='initial_stock',
                                          quantity=initial, unit=product.unit or 'unit',
                                          stock_before=Decimal('0'), stock_after=initial,
                                          reason='Stock initial', reference_document=product.reference))
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception:
            self.db.rollback()
            raise

    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        data = self._validate_data(product_data)
        if 'unit' in data and data['unit'] != product.unit:
            from models.inventory import Inventory, InventoryLine
            inventory_exists = self.db.query(InventoryLine.id).join(Inventory).filter(
                InventoryLine.product_id == product.id).first()
            if product.packagings or product.stock_movements or product.stock_quantity != 0 or inventory_exists:
                raise ValueError('L’unité de base ne peut pas être changée lorsqu’un historique ou un conditionnement existe.')
        for key, value in data.items():
            setattr(product, key, value)
        try:
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception:
            self.db.rollback()
            raise

    def deactivate_product(self, product_id: int) -> bool:
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        product.is_active = False
        self.db.commit()
        return True
    
    def get_all_categories(self, include_inactive: bool = False) -> List[Category]:
        query = self.db.query(Category)
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        return query.all()
    
    def create_category(self, name: str, description: str = None) -> Category:
        category = Category(name=name, description=description)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def _generate_reference(self) -> str:
        return f"PROD-{uuid4().hex.upper()}"