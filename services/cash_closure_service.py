from sqlalchemy.orm import Session
from models.cash import CashRegister, CashClosure
from services.sales_service import SalesService
from services.expense_service import ExpenseService
from datetime import datetime, timedelta
from typing import Optional, List


class CashClosureService:
    def __init__(self, db: Session):
        self.db = db
        self.sales_service = SalesService(db)
        self.expense_service = ExpenseService(db)
    
    def get_daily_sales(self, date: datetime) -> List:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return self.sales_service.get_sales_by_date_range(start_of_day, end_of_day)
    
    def get_daily_expenses(self, date: datetime) -> List:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return self.expense_service.get_expenses_by_date_range(start_of_day, end_of_day)
    
    def calculate_daily_totals(self, date: datetime) -> dict:
        sales = self.get_daily_sales(date)
        expenses = self.get_daily_expenses(date)
        
        total_sales = sum(s.total_amount for s in sales if s.status.value == 'completed')
        total_expenses = sum(e.amount for e in expenses)
        
        return {
            'date': date,
            'total_sales': total_sales,
            'total_expenses': total_expenses,
            'net_profit': total_sales - total_expenses,
            'sales_count': len(sales),
            'expenses_count': len(expenses)
        }
    
    def create_cash_closure(self, closure_data: dict) -> CashClosure:
        closure = CashClosure(**closure_data)
        self.db.add(closure)
        self.db.commit()
        self.db.refresh(closure)
        return closure
    
    def get_latest_cash_closure(self) -> Optional[CashClosure]:
        return self.db.query(CashClosure).order_by(CashClosure.closure_date.desc()).first()
    
    def get_cash_closure_by_date(self, date: datetime) -> Optional[CashClosure]:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return self.db.query(CashClosure).filter(
            CashClosure.closure_date >= start_of_day,
            CashClosure.closure_date < end_of_day
        ).first()