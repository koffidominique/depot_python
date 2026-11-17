from sqlalchemy.orm import Session
from models.purchase import PurchaseOrder, PurchaseOrderLine
from models.product import Product
from services.stock_service import StockService
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class PurchaseService:
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
    
    def get_all_purchase_orders(self, include_cancelled: bool = False) -> List[PurchaseOrder]:
        query = self.db.query(PurchaseOrder)
        if not include_cancelled:
            query = query.filter(PurchaseOrder.is_cancelled == False)
        return query.order_by(PurchaseOrder.date.desc()).all()
    
    def get_purchase_order_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    
    def create_purchase_order(self, order_data: dict, order_lines_data: List[dict], user_id: int = None) -> Optional[PurchaseOrder]:
        reference = self._generate_order_reference()
        
        total_amount = Decimal('0.0')
        
        order = PurchaseOrder(
            reference=reference,
            supplier_id=order_data.get('supplier_id'),
            order_date=order_data.get('order_date'),
            expected_date=order_data.get('expected_date'),
            status='draft',
            user_id=user_id
        )
        
        self.db.add(order)
        self.db.flush()
        
        for line_data in order_lines_data:
            product = self.db.query(Product).filter(Product.id == line_data['product_id']).first()
            if not product:
                self.db.rollback()
                return None
            
            ordered_quantity = Decimal(str(line_data['ordered_quantity']))
            unit_price = Decimal(str(line_data['unit_price']))
            
            line_total = ordered_quantity * unit_price
            total_amount += line_total
            
            order_line = PurchaseOrderLine(
                purchase_order_id=order.id,
                product_id=product.id,
                ordered_quantity=ordered_quantity,
                unit_price=unit_price,
                line_total=line_total
            )
            self.db.add(order_line)
        
        order.total_amount = total_amount
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def receive_purchase_order(self, order_id: int, receive_lines_data: List[dict], user_id: int = None) -> bool:
        order = self.get_purchase_order_by_id(order_id)
        if not order or order.is_cancelled:
            return False
        
        total_received = Decimal('0.0')
        
        for line_data in receive_lines_data:
            line_id = line_data.get('line_id')
            received_quantity = Decimal(str(line_data.get('received_quantity')))
            
            line = self.db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == line_id).first()
            if not line:
                continue
            
            line.received_quantity += received_quantity
            total_received += received_quantity * line.unit_price
            
            stock_change = received_quantity
            self.stock_service.update_stock(
                product_id=line.product_id,
                quantity_change=stock_change,
                movement_type='purchase_reception',
                user_id=user_id,
                reference_document=order.reference
            )
        
        order.received_amount += total_received
        
        all_lines_received = all(line.received_quantity >= line.ordered_quantity for line in order.purchase_order_lines)
        if all_lines_received:
            order.status = 'received'
        else:
            order.status = 'partially_received'
        
        self.db.commit()
        return True
    
    def validate_purchase_order(self, order_id: int, user_id: int = None) -> bool:
        order = self.get_purchase_order_by_id(order_id)
        if not order or order.is_cancelled:
            return False
        order.status = 'validated'
        self.db.commit()
        return True
    
    def cancel_purchase_order(self, order_id: int, user_id: int = None) -> bool:
        order = self.get_purchase_order_by_id(order_id)
        if not order or order.is_cancelled:
            return False
        order.is_cancelled = True
        order.status = 'cancelled'
        self.db.commit()
        return True
    
    def _generate_order_reference(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CMD-{timestamp}"