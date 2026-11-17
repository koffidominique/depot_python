from sqlalchemy.orm import Session
from models.consignation import Consignation
from models.client import Client
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from enums import ConsignationItemType

class ConsignationService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_consignation(self, client_id: int, item_type: str, quantity_out: Decimal, unit_value: Decimal, sale_id: int = None, notes: str = None) -> Consignation:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client non trouvé")
        
        total_value = quantity_out * unit_value
        
        consignation = Consignation(
            client_id=client_id,
            sale_id=sale_id,
            item_type=item_type,
            quantity_out=quantity_out,
            quantity_remaining=quantity_out,
            unit_value=unit_value,
            total_value=total_value,
            status='outstanding',
            notes=notes,
            date_out=datetime.now()
        )
        
        self.db.add(consignation)
        self.db.commit()
        self.db.refresh(consignation)
        return consignation
    
    def get_consignation_by_id(self, consignation_id: int) -> Optional[Consignation]:
        return self.db.query(Consignation).filter(Consignation.id == consignation_id).first()
    
    def return_consignation_items(self, consignation_id: int, quantity_returned: Decimal, notes: str = None) -> Optional[Consignation]:
        consignation = self.get_consignation_by_id(consignation_id)
        if not consignation:
            return None
        
        if quantity_returned > consignation.quantity_remaining:
            quantity_returned = consignation.quantity_remaining
        
        consignation.quantity_returned += quantity_returned
        consignation.quantity_remaining -= quantity_returned
        
        if notes:
            consignation.notes = notes
        
        if consignation.quantity_remaining <= 0:
            consignation.status = 'returned'
            consignation.date_return = datetime.now()
        
        self.db.commit()
        self.db.refresh(consignation)
        return consignation
    
    def get_all_consignations(self, status: str = None) -> List[Consignation]:
        query = self.db.query(Consignation)
        if status:
            query = query.filter(Consignation.status == status)
        return query.order_by(Consignation.date_out.desc()).all()
    
    def get_client_consignations(self, client_id: int, status: str = None) -> List[Consignation]:
        query = self.db.query(Consignation).filter(Consignation.client_id == client_id)
        if status:
            query = query.filter(Consignation.status == status)
        return query.order_by(Consignation.date_out.desc()).all()
    
    def delete_consignation(self, consignation_id: int) -> bool:
        consignation = self.get_consignation_by_id(consignation_id)
        if not consignation:
            return False
        
        self.db.delete(consignation)
        self.db.commit()
        return True