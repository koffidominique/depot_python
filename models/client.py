from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    type = Column(String, default="particulier")
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    email = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    credit_limit = Column(Numeric(precision=10, scale=2), default=0.0)
    financial_balance = Column(Numeric(precision=10, scale=2), default=0.0)
    consignment_balance = Column(Numeric(precision=10, scale=3), default=0.0)
    payment_terms = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sales = relationship("Sale", back_populates="client")
    client_debts = relationship("ClientDebt", back_populates="client")
    consignations = relationship("Consignation", back_populates="client")
    deliveries = relationship("Delivery", back_populates="client")