from sqlalchemy import Column, Integer, String, Boolean, Text, Numeric, DateTime, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    type = Column(String, default="particulier", nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    email = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    credit_limit = Column(Numeric(precision=10, scale=2), default=0.0, nullable=False)
    financial_balance = Column(Numeric(precision=10, scale=2), default=0.0, nullable=False)
    consignment_balance = Column(Numeric(precision=10, scale=3), default=0.0, nullable=False)
    payment_terms = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    sales = relationship("Sale", back_populates="client")
    client_debts = relationship("ClientDebt", back_populates="client")
    consignations = relationship("Consignation", back_populates="client")
    deliveries = relationship("Delivery", back_populates="client")
    
    __table_args__ = (
        CheckConstraint('LENGTH(code) > 0', name='check_client_code_not_empty'),
        CheckConstraint('LENGTH(name) > 0', name='check_client_name_not_empty'),
        CheckConstraint('type IN (\'particulier\', \'professionnel\')', name='check_client_type_valid'),
        CheckConstraint('credit_limit >= 0', name='check_client_credit_limit_positive'),
        CheckConstraint('payment_terms >= 0', name='check_client_payment_terms_non_negative'),
        Index('idx_client_type', 'type'),
        Index('idx_client_is_active', 'is_active'),
    )