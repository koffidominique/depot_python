from money import CFAAmount
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    payment_terms = Column(Integer, default=0)
    balance_due = Column(CFAAmount(), default=0.0)
    total_purchases = Column(CFAAmount(), default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    supplier_debts = relationship("SupplierDebt", back_populates="supplier")
    
    __table_args__ = (
        CheckConstraint('LENGTH(code) > 0', name='check_supplier_code_not_empty'),
        CheckConstraint('LENGTH(name) > 0', name='check_supplier_name_not_empty'),
        CheckConstraint('LENGTH(phone) > 0', name='check_supplier_phone_not_empty'),
        CheckConstraint('balance_due >= 0', name='check_supplier_balance_due_positive'),
        CheckConstraint('total_purchases >= 0', name='check_supplier_total_purchases_positive'),
        Index('idx_supplier_is_active', 'is_active'),
    )