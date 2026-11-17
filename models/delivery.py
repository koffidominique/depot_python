from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Delivery(Base):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    date = Column(DateTime, default=datetime.utcnow)
    scheduled_date = Column(DateTime, nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_person = Column(String, nullable=True)
    transport_cost = Column(Numeric(precision=10, scale=2), default=0.0)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    sale = relationship("Sale", back_populates="deliveries")
    client = relationship("Client", back_populates="deliveries")