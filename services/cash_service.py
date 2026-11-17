from sqlalchemy.orm import Session
from models.cash import CashSession, CashMovement
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

class CashService:
    def __init__(self, db: Session):
        self.db = db
    
    def open_cash_session(self, initial_cash: Decimal, user_id: int) -> CashSession:
        cash_session = CashSession(
            initial_cash=initial_cash,
            theoretical_balance=initial_cash,
            status='open',
            user_id=user_id,
            opening_date=datetime.now()
        )
        
        self.db.add(cash_session)
        self.db.commit()
        self.db.refresh(cash_session)
        return cash_session
    
    def close_cash_session(self, cash_session_id: int, physical_balance: Decimal, user_id: int, closing_notes: str = None) -> Optional[CashSession]:
        cash_session = self.get_cash_session_by_id(cash_session_id)
        if not cash_session:
            return None
        
        cash_session.physical_balance = physical_balance
        cash_session.difference = physical_balance - cash_session.theoretical_balance
        cash_session.status = 'closed'
        cash_session.user_id = user_id
        cash_session.closing_notes = closing_notes
        cash_session.closing_date = datetime.now()
        
        self.db.commit()
        self.db.refresh(cash_session)
        return cash_session
    
    def get_cash_session_by_id(self, cash_session_id: int) -> Optional[CashSession]:
        return self.db.query(CashSession).filter(CashSession.id == cash_session_id).first()
    
    def get_open_cash_session(self) -> Optional[CashSession]:
        return self.db.query(CashSession).filter(CashSession.status == 'open').order_by(CashSession.opening_date.desc()).first()
    
    def create_cash_movement(self, cash_session_id: int, movement_type: str, amount: Decimal, payment_method: str = None, reference: str = None, notes: str = None, user_id: int = None) -> CashMovement:
        cash_session = self.get_cash_session_by_id(cash_session_id)
        if not cash_session:
            raise ValueError("Session de caisse non trouvée")
        
        movement = CashMovement(
            cash_session_id=cash_session_id,
            movement_type=movement_type,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            user_id=user_id,
            date=datetime.now()
        )
        
        if movement_type == 'income':
            if payment_method == 'cash':
                cash_session.total_cash_sales += amount
            elif payment_method == 'mobile_money':
                cash_session.total_mobile_money += amount
            elif payment_method == 'transfer':
                cash_session.total_transfers += amount
            else:
                cash_session.total_other += amount
            cash_session.theoretical_balance += amount
        elif movement_type == 'expense':
            cash_session.total_expenses += amount
            cash_session.theoretical_balance -= amount
        
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement
    
    def get_cash_movements(self, cash_session_id: int) -> List[CashMovement]:
        return self.db.query(CashMovement).filter(CashMovement.cash_session_id == cash_session_id).order_by(CashMovement.date.desc()).all()
    
    def get_all_cash_sessions(self, status: str = None) -> List[CashSession]:
        query = self.db.query(CashSession)
        if status:
            query = query.filter(CashSession.status == status)
        return query.order_by(CashSession.opening_date.desc()).all()