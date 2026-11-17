from sqlalchemy.orm import Session
from models.debt import ClientDebt
from models.client import Client
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class DebtService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_client_debt(self, client_id: int, amount: Decimal, reason: str = None, due_date: datetime = None) -> ClientDebt:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client non trouvé")
        
        debt = ClientDebt(
            client_id=client_id,
            initial_amount=amount,
            remaining_amount=amount,
            due_date=due_date,
            status='pending'
        )
        
        client.balance += amount
        
        self.db.add(debt)
        self.db.commit()
        self.db.refresh(debt)
        return debt
    
    def get_client_debt_by_id(self, debt_id: int) -> Optional[ClientDebt]:
        return self.db.query(ClientDebt).filter(ClientDebt.id == debt_id).first()
    
    def get_client_debts(self, client_id: int, status: str = None) -> List[ClientDebt]:
        query = self.db.query(ClientDebt).filter(ClientDebt.client_id == client_id)
        if status:
            query = query.filter(ClientDebt.status == status)
        return query.order_by(ClientDebt.date.desc()).all()
    
    def pay_client_debt(self, debt_id: int, amount: Decimal) -> Optional[ClientDebt]:
        debt = self.get_client_debt_by_id(debt_id)
        if not debt:
            return None
        
        if amount > debt.remaining_amount:
            amount = debt.remaining_amount
        
        debt.paid_amount += amount
        debt.remaining_amount -= amount
        
        client = debt.client
        if client:
            client.balance -= amount
        
        if debt.remaining_amount <= 0:
            debt.status = 'paid'
        
        self.db.commit()
        self.db.refresh(debt)
        return debt
    
    def get_all_client_debts(self, status: str = None) -> List[ClientDebt]:
        query = self.db.query(ClientDebt)
        if status:
            query = query.filter(ClientDebt.status == status)
        return query.order_by(ClientDebt.date.desc()).all()
    
    def delete_client_debt(self, debt_id: int) -> bool:
        debt = self.get_client_debt_by_id(debt_id)
        if not debt:
            return False
        
        client = debt.client
        if client:
            client.balance -= debt.remaining_amount
        
        self.db.delete(debt)
        self.db.commit()
        return True