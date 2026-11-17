from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Consignation(Base):
    __tablename__ = "consignations"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    total_value = Column(Numeric(precision=10, scale=2), nullable=False)
    delivered_quantity = Column(Numeric(precision=10, scale=3), default=0.0)
    remaining_quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    client = relationship("Client", back_populates="consignations")
    consignation_lines = relationship("ConsignationLine", back_populates="consignation")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_consignation_reference_not_empty'),
        CheckConstraint('total_quantity > 0', name='check_consignation_total_quantity_positive'),
        CheckConstraint('total_value >= 0', name='check_consignation_total_value_positive'),
        CheckConstraint('delivered_quantity >= 0', name='check_consignation_delivered_quantity_positive'),
        CheckConstraint('remaining_quantity >= 0', name='check_consignation_remaining_quantity_positive'),
        Index('idx_consignation_client', 'client_id'),
        Index('idx_consignation_date', 'date'),
        Index('idx_consignation_status', 'status'),
    )

class ConsignationLine(Base):
    __tablename__ = "consignation_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    consignation_id = Column(Integer, ForeignKey("consignations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    line_total = Column(Numeric(precision=10, scale=2), nullable=False)
    
    consignation = relationship("Consignation", back_populates="consignation_lines")
    product = relationship("Product", back_populates="consignation_lines")
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_consignation_line_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_consignation_line_unit_price_positive'),
        CheckConstraint('line_total >= 0', name='check_consignation_line_total_positive'),
        Index('idx_consignation_line_consignation', 'consignation_id'),
        Index('idx_consignation_line_product', 'product_id'),
    )