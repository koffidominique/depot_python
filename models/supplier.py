from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    company_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    payment_terms = Column(Integer, default=0)
    balance_due = Column(Numeric(precision=10, scale=2), default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    supplier_debts = relationship("SupplierDebt", back_populates="supplier")