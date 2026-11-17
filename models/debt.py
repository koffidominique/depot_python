from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class ClientDebt(Base):
    __tablename__ = "client_debts"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    initial_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    paid_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    remaining_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    is_cancelled = Column(Boolean, default=False)
    
    client = relationship("Client", back_populates="client_debts")
    payments = relationship("Payment", back_populates="client_debt")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_client_debt_reference_not_empty'),
        CheckConstraint('initial_amount >= 0', name='check_client_debt_initial_amount_positive'),
        CheckConstraint('paid_amount >= 0', name='check_client_debt_paid_amount_positive'),
        CheckConstraint('remaining_amount >= 0', name='check_client_debt_remaining_amount_positive'),
        Index('idx_client_debt_client', 'client_id'),
        Index('idx_client_debt_date', 'date'),
        Index('idx_client_debt_status', 'status'),
    )

class SupplierDebt(Base):
    __tablename__ = "supplier_debts"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    initial_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    paid_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    remaining_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    is_cancelled = Column(Boolean, default=False)
    
    supplier = relationship("Supplier", back_populates="supplier_debts")
    payments = relationship("Payment", back_populates="supplier_debt")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_supplier_debt_reference_not_empty'),
        CheckConstraint('initial_amount >= 0', name='check_supplier_debt_initial_amount_positive'),
        CheckConstraint('paid_amount >= 0', name='check_supplier_debt_paid_amount_positive'),
        CheckConstraint('remaining_amount >= 0', name='check_supplier_debt_remaining_amount_positive'),
        Index('idx_supplier_debt_supplier', 'supplier_id'),
        Index('idx_supplier_debt_date', 'date'),
        Index('idx_supplier_debt_status', 'status'),
    )