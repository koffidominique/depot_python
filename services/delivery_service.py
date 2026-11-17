from sqlalchemy.orm import Session
from models.delivery import Delivery
from models.sale import Sale
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_delivery(self, sale_id: int, delivery_address: str = None, scheduled_date: datetime = None, delivery_person: str = None, transport_cost: Decimal = Decimal('0'), notes: str = None) -> Delivery:
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError("Vente non trouvée")
        
        delivery = Delivery(
            sale_id=sale_id,
            client_id=sale.client_id,
            delivery_address=delivery_address,
            scheduled_date=scheduled_date,
            delivery_person=delivery_person,
            transport_cost=transport_cost,
            status='pending',
            notes=notes,
            date=datetime.now()
        )
        
        self.db.add(delivery)
        sale.status = 'delivering'
        self.db.commit()
        self.db.refresh(delivery)
        return delivery
    
    def get_delivery_by_id(self, delivery_id: int) -> Optional[Delivery]:
        return self.db.query(Delivery).filter(Delivery.id == delivery_id).first()
    
    def get_sale_delivery(self, sale_id: int) -> Optional[Delivery]:
        return self.db.query(Delivery).filter(Delivery.sale_id == sale_id).first()
    
    def update_delivery_status(self, delivery_id: int, status: str, notes: str = None) -> Optional[Delivery]:
        delivery = self.get_delivery_by_id(delivery_id)
        if not delivery:
            return None
        
        delivery.status = status
        if notes:
            delivery.notes = notes
        
        if status == 'delivered':
            sale = delivery.sale
            if sale:
                sale.status = 'completed'
        
        self.db.commit()
        self.db.refresh(delivery)
        return delivery
    
    def get_all_deliveries(self, status: str = None) -> List[Delivery]:
        query = self.db.query(Delivery)
        if status:
            query = query.filter(Delivery.status == status)
        return query.order_by(Delivery.date.desc()).all()
    
    def delete_delivery(self, delivery_id: int) -> bool:
        delivery = self.get_delivery_by_id(delivery_id)
        if not delivery:
            return False
        
        sale = delivery.sale
        if sale:
            sale.status = 'confirmed'
        
        self.db.delete(delivery)
        self.db.commit()
        return True