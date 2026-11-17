from sqlalchemy.orm import Session
from models.supplier import Supplier
from typing import List, Optional
from datetime import datetime

class SupplierService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_suppliers(self, include_inactive: bool = False) -> List[Supplier]:
        query = self.db.query(Supplier)
        if not include_inactive:
            query = query.filter(Supplier.is_active == True)
        return query.all()
    
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(Supplier.code == code).first()
    
    def search_suppliers(self, search_term: str) -> List[Supplier]:
        return self.db.query(Supplier).filter(
            Supplier.name.ilike(f"%{search_term}%") |
            Supplier.code.ilike(f"%{search_term}%") |
            Supplier.phone.ilike(f"%{search_term}%")
        ).all()
    
    def create_supplier(self, supplier_data: dict) -> Supplier:
        code = self._generate_supplier_code()
        supplier = Supplier(code=code, **supplier_data)
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier
    
    def update_supplier(self, supplier_id: int, supplier_data: dict) -> Optional[Supplier]:
        supplier = self.get_supplier_by_id(supplier_id)
        if not supplier:
            return None
        for key, value in supplier_data.items():
            setattr(supplier, key, value)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier
    
    def deactivate_supplier(self, supplier_id: int) -> bool:
        supplier = self.get_supplier_by_id(supplier_id)
        if not supplier:
            return False
        supplier.is_active = False
        self.db.commit()
        return True
    
    def get_total_supplier_debts(self) -> float:
        suppliers = self.db.query(Supplier).filter(Supplier.is_active == True).all()
        total = sum(supplier.balance_due for supplier in suppliers)
        return total
    
    def _generate_supplier_code(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"FOUR-{timestamp}"