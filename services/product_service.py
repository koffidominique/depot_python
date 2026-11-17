from sqlalchemy.orm import Session
from models.product import Product, Category
from typing import List, Optional
from datetime import datetime

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_products(self, include_inactive: bool = False) -> List[Product]:
        query = self.db.query(Product)
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        return query.all()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_reference(self, reference: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.reference == reference).first()
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    
    def create_product(self, product_data: dict) -> Product:
        reference = self._generate_reference()
        product = Product(reference=reference, **product_data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        for key, value in product_data.items():
            setattr(product, key, value)
        self.db.commit()
        self.db.refresh(product)
        return product
    
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
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PROD-{timestamp}"