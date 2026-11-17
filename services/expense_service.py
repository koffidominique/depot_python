from sqlalchemy.orm import Session
from models.expense import Expense
from typing import List, Optional
from datetime import datetime


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_expenses(self) -> List[Expense]:
        return self.db.query(Expense).all()
    
    def get_expenses_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Expense]:
        return self.db.query(Expense).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).all()
    
    def get_expense_by_id(self, expense_id: int) -> Optional[Expense]:
        return self.db.query(Expense).filter(Expense.id == expense_id).first()
    
    def create_expense(self, expense_data: dict) -> Expense:
        expense = Expense(**expense_data)
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def update_expense(self, expense_id: int, expense_data: dict) -> Optional[Expense]:
        expense = self.get_expense_by_id(expense_id)
        if expense:
            for key, value in expense_data.items():
                setattr(expense, key, value)
            self.db.commit()
            self.db.refresh(expense)
        return expense
    
    def delete_expense(self, expense_id: int) -> bool:
        expense = self.get_expense_by_id(expense_id)
        if expense:
            self.db.delete(expense)
            self.db.commit()
            return True
        return False
    
    def get_total_expenses_by_date_range(self, start_date: datetime, end_date: datetime) -> float:
        expenses = self.get_expenses_by_date_range(start_date, end_date)
        return sum(e.amount for e in expenses)