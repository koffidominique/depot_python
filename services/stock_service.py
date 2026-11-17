from sqlalchemy.orm import Session
from sqlalchemy import func
from models.product import Product
from models.stock import StockMovement
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

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
                     reference_document: str = None) -> bool:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        stock_before = product.stock_quantity
        stock_after = stock_before + quantity_change
        
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
        self.db.commit()
        return True
    
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