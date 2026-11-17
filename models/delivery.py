from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Delivery(Base):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_person = Column(String, nullable=True)
    transport_cost = Column(Numeric(precision=10, scale=2), default=0.0)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    sale = relationship("Sale", back_populates="deliveries")
    client = relationship("Client", back_populates="deliveries")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_delivery_reference_not_empty'),
        CheckConstraint('transport_cost >= 0', name='check_delivery_transport_cost_positive'),
        Index('idx_delivery_sale', 'sale_id'),
        Index('idx_delivery_client', 'client_id'),
        Index('idx_delivery_date', 'date'),
        Index('idx_delivery_status', 'status'),
    )