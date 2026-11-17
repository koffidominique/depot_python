from sqlalchemy.orm import Session
from models.payment import Payment
from models.sale import Sale
from models.client import Client
from models.debt import ClientDebt
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class PaymentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_sale_payment(self, sale_id: int, amount: Decimal, payment_method: str, reference: str = None, notes: str = None, user_id: int = None) -> Payment:
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError("Vente non trouvée")
        
        payment = Payment(
            sale_id=sale_id,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            user_id=user_id,
            date=datetime.now()
        )
        
        self.db.add(payment)
        
        if sale.client_id:
            client = self.db.query(Client).filter(Client.id == sale.client_id).first()
            if client:
                client.balance -= amount
        
        self.db.commit()
        self.db.refresh(payment)
        
        total_paid = sum(p.amount for p in sale.payments)
        if total_paid >= sale.total_amount:
            sale.payment_status = 'paid'
            self.db.commit()
        
        return payment
    
    def create_debt_payment(self, client_debt_id: int, amount: Decimal, payment_method: str, reference: str = None, notes: str = None, user_id: int = None) -> Payment:
        debt = self.db.query(ClientDebt).filter(ClientDebt.id == client_debt_id).first()
        if not debt:
            raise ValueError("Dette client non trouvée")
        
        payment = Payment(
            client_debt_id=client_debt_id,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            user_id=user_id,
            date=datetime.now()
        )
        
        self.db.add(payment)
        
        debt.paid_amount += amount
        debt.remaining_amount -= amount
        
        client = debt.client
        if client:
            client.balance -= amount
        
        if debt.remaining_amount <= 0:
            debt.status = 'paid'
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_sale_payments(self, sale_id: int) -> List[Payment]:
        return self.db.query(Payment).filter(Payment.sale_id == sale_id).all()
    
    def get_client_payments(self, client_id: int) -> List[Payment]:
        return self.db.query(Payment).join(Sale).filter(Sale.client_id == client_id).all()
    
    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def delete_payment(self, payment_id: int) -> bool:
        payment = self.get_payment_by_id(payment_id)
        if not payment:
            return False
        
        if payment.supplier_debt_id is not None or payment.cash_link_status == 'linked_cash':
            raise ValueError('Un règlement fournisseur ne peut pas être supprimé : une procédure de contrepassation est nécessaire.')
        if payment.sale_id:
            sale = payment.sale
            if sale and sale.client_id:
                client = self.db.query(Client).filter(Client.id == sale.client_id).first()
                if client:
                    client.balance += payment.amount
            
            total_paid = sum(p.amount for p in sale.payments if p.id != payment_id)
            if total_paid < sale.total_amount:
                sale.payment_status = 'pending'
        
        elif payment.client_debt_id:
            debt = payment.client_debt
            if debt:
                debt.paid_amount -= payment.amount
                debt.remaining_amount += payment.amount
                client = debt.client
                if client:
                    client.balance += payment.amount
                debt.status = 'pending'
        
        self.db.delete(payment)
        self.db.commit()
        return True
    
    def get_all_payments(self, start_date: datetime = None, end_date: datetime = None) -> List[Payment]:
        query = self.db.query(Payment)
        if start_date:
            query = query.filter(Payment.date >= start_date)
        if end_date:
            query = query.filter(Payment.date <= end_date)
        return query.order_by(Payment.date.desc()).all()