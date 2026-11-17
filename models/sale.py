from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    discount_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    tax_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    consignment_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    net_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    amount_paid = Column(Numeric(precision=10, scale=2), default=0.0)
    remaining_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    payment_status = Column(String, default="pending")
    sale_status = Column(String, default="draft")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    client = relationship("Client", back_populates="sales")
    sale_lines = relationship("SaleLine", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    deliveries = relationship("Delivery", back_populates="sale")

class SaleLine(Base):
    __tablename__ = "sale_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Numeric(precision=10, scale=3))
    unit_price = Column(Numeric(precision=10, scale=2))
    discount = Column(Numeric(precision=10, scale=2), default=0.0)
    consignment = Column(Numeric(precision=10, scale=2), default=0.0)
    line_total = Column(Numeric(precision=10, scale=2))
    
    sale = relationship("Sale", back_populates="sale_lines")
    product = relationship("Product", back_populates="sale_lines")