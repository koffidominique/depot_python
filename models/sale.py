from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
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
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_sale_reference_not_empty'),
        CheckConstraint('total_amount >= 0', name='check_sale_total_amount_positive'),
        CheckConstraint('discount_amount >= 0', name='check_sale_discount_amount_positive'),
        CheckConstraint('tax_amount >= 0', name='check_sale_tax_amount_positive'),
        CheckConstraint('net_amount >= 0', name='check_sale_net_amount_positive'),
        CheckConstraint('amount_paid >= 0', name='check_sale_amount_paid_positive'),
        CheckConstraint('remaining_amount >= 0', name='check_sale_remaining_amount_positive'),
        Index('idx_sale_client', 'client_id'),
        Index('idx_sale_date', 'date'),
        Index('idx_sale_status', 'sale_status'),
        Index('idx_sale_payment_status', 'payment_status'),
    )

class SaleLine(Base):
    __tablename__ = "sale_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    discount = Column(Numeric(precision=10, scale=2), default=0.0)
    consignment = Column(Numeric(precision=10, scale=2), default=0.0)
    line_total = Column(Numeric(precision=10, scale=2), nullable=False)
    
    sale = relationship("Sale", back_populates="sale_lines")
    product = relationship("Product", back_populates="sale_lines")
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_sale_line_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_sale_line_unit_price_positive'),
        CheckConstraint('discount >= 0', name='check_sale_line_discount_positive'),
        CheckConstraint('line_total >= 0', name='check_sale_line_total_positive'),
        Index('idx_sale_line_sale', 'sale_id'),
        Index('idx_sale_line_product', 'product_id'),
    )