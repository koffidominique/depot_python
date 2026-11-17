from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class ClientDebt(Base):
    __tablename__ = "client_debts"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    initial_amount = Column(Numeric(precision=10, scale=2))
    paid_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    remaining_amount = Column(Numeric(precision=10, scale=2))
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    is_cancelled = Column(Boolean, default=False)
    
    client = relationship("Client", back_populates="client_debts")
    payments = relationship("Payment", back_populates="client_debt")

class SupplierDebt(Base):
    __tablename__ = "supplier_debts"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    initial_amount = Column(Numeric(precision=10, scale=2))
    paid_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    remaining_amount = Column(Numeric(precision=10, scale=2))
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    is_cancelled = Column(Boolean, default=False)
    
    supplier = relationship("Supplier", back_populates="supplier_debts")
    payments = relationship("Payment", back_populates="supplier_debt")