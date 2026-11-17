from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    client_debt_id = Column(Integer, ForeignKey("client_debts.id"), nullable=True)
    supplier_debt_id = Column(Integer, ForeignKey("supplier_debts.id"), nullable=True)
    amount = Column(Numeric(precision=10, scale=2))
    payment_method = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    sale = relationship("Sale", back_populates="payments")
    client_debt = relationship("ClientDebt", back_populates="payments")
    supplier_debt = relationship("SupplierDebt", back_populates="payments")