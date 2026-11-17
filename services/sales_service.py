from sqlalchemy.orm import Session
from sqlalchemy import func
from models.sale import Sale, SaleLine
from models.product import Product
from models.client import Client
from services.stock_service import StockService
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class SalesService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
    
    def get_all_sales(self, include_cancelled: bool = False) -> List[Sale]:
        query = self.db.query(Sale)
        if not include_cancelled:
            query = query.filter(Sale.is_cancelled == False)
        return query.order_by(Sale.date.desc()).all()
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        return self.db.query(Sale).filter(Sale.id == sale_id).first()
    
    def create_sale(self, sale_data: dict, sale_lines_data: List[dict], user_id: int = None) -> Optional[Sale]:
        reference = self._generate_sale_reference()
        
        total_amount = Decimal('0.0')
        discount_amount = Decimal('0.0')
        tax_amount = Decimal('0.0')
        consignment_amount = Decimal('0.0')
        net_amount = Decimal('0.0')
        
        sale = Sale(
            reference=reference,
            client_id=sale_data.get('client_id'),
            user_id=user_id,
            sale_status='validated',
            payment_status='pending'
        )
        
        self.db.add(sale)
        self.db.flush()
        
        for line_data in sale_lines_data:
            product = self.db.query(Product).filter(Product.id == line_data['product_id']).first()
            if not product:
                self.db.rollback()
                return None
            
            quantity = Decimal(str(line_data['quantity']))
            unit_price = Decimal(str(line_data['unit_price']))
            discount = Decimal(str(line_data.get('discount', 0.0)))
            consignment = Decimal(str(line_data.get('consignment', 0.0)))
            
            line_total = quantity * unit_price - discount
            total_amount += line_total
            consignment_amount += consignment
            
            sale_line = SaleLine(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                consignment=consignment,
                line_total=line_total
            )
            self.db.add(sale_line)
            
            stock_change = -quantity
            self.stock_service.update_stock(
                product_id=product.id,
                quantity_change=stock_change,
                movement_type='sale',
                user_id=user_id,
                reference_document=reference
            )
        
        net_amount = total_amount + consignment_amount
        sale.total_amount = total_amount
        sale.discount_amount = discount_amount
        sale.tax_amount = tax_amount
        sale.consignment_amount = consignment_amount
        sale.net_amount = net_amount
        sale.remaining_amount = net_amount
        
        self.db.commit()
        self.db.refresh(sale)
        return sale
    
    def add_payment_to_sale(self, sale_id: int, amount: Decimal, payment_method: str, user_id: int = None) -> bool:
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            return False
        
        sale.amount_paid += amount
        sale.remaining_amount -= amount
        
        if sale.remaining_amount <= 0:
            sale.payment_status = 'paid'
        
        self.db.commit()
        return True
    
    def cancel_sale(self, sale_id: int, user_id: int = None) -> bool:
        sale = self.get_sale_by_id(sale_id)
        if not sale or sale.is_cancelled:
            return False
        
        sale.is_cancelled = True
        sale.sale_status = 'cancelled'
        
        for line in sale.sale_lines:
            stock_change = line.quantity
            self.stock_service.update_stock(
                product_id=line.product_id,
                quantity_change=stock_change,
                movement_type='sale_cancellation',
                user_id=user_id,
                reference_document=sale.reference
            )
        
        self.db.commit()
        return True
    
    def get_daily_sales_total(self, date: datetime = None) -> Decimal:
        if not date:
            date = datetime.now().date()
        
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        result = self.db.query(func.sum(Sale.total_amount)).filter(
            Sale.date >= start_of_day,
            Sale.date <= end_of_day,
            Sale.is_cancelled == False
        ).scalar()
        
        return result if result else Decimal('0.0')
    
    def _generate_sale_reference(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"VTE-{timestamp}"