from sqlalchemy.orm import Session
from sqlalchemy import func
from models.product import Product
from models.stock import StockMovement
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from logger import log_error, log_business

class StockService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_stock_by_product_id(self, product_id: int) -> Optional[Decimal]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            return product.stock_quantity
        return None
    
    def update_stock(self, product_id: int, quantity_change: Decimal, movement_type: str, 
                     unit: str = "unit", user_id: int = None, reason: str = None, 
                     reference_document: str = None, allow_negative_stock: bool = False,
                     commit: bool = True) -> bool:
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                log_error(f"Produit {product_id} non trouvé lors de la mise à jour du stock")
                return False
            
            stock_before = product.stock_quantity
            stock_after = stock_before + quantity_change
            
            if not allow_negative_stock and stock_after < Decimal('0'):
                log_error(f"Stock négatif interdit pour le produit {product_id}: {stock_after}")
                return False
            
            movement = StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity_change,
                unit=unit,
                stock_before=stock_before,
                stock_after=stock_after,
                user_id=user_id,
                reason=reason,
                reference_document=reference_document
            )
            
            product.stock_quantity = stock_after
            
            self.db.add(movement)
            self.db.flush()
            
            if commit:
                self.db.commit()
                log_business(f"Mouvement de stock", f"Produit {product_id}: {stock_before} -> {stock_after} (type: {movement_type})")
            
            return True
        except Exception as e:
            log_error(f"Erreur lors de la mise à jour du stock pour le produit {product_id}: {str(e)}")
            if commit:
                self.db.rollback()
            return False
    
    def get_low_stock_products(self) -> List[Product]:
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock_quantity <= Product.min_stock
        ).all()
    
    def get_out_of_stock_products(self) -> List[Product]:
        return self.db.query(Product).filter(
            Product.is_active == True,
            Product.stock_quantity <= 0
        ).all()
    
    def get_stock_movements(self, product_id: int = None, limit: int = 100) -> List[StockMovement]:
        query = self.db.query(StockMovement)
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        return query.order_by(StockMovement.date.desc()).limit(limit).all()
    
    def get_total_stock_value(self) -> Decimal:
        products = self.db.query(Product).filter(Product.is_active == True).all()
        total_value = Decimal('0.0')
        for product in products:
            total_value += product.stock_quantity * product.purchase_price
        return total_value