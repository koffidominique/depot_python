from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Consignation(Base):
    __tablename__ = "consignations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)
    date_out = Column(DateTime, default=datetime.utcnow)
    date_return = Column(DateTime, nullable=True)
    item_type = Column(String)
    quantity_out = Column(Numeric(precision=10, scale=3))
    quantity_returned = Column(Numeric(precision=10, scale=3), default=0.0)
    quantity_remaining = Column(Numeric(precision=10, scale=3))
    unit_value = Column(Numeric(precision=10, scale=2))
    total_value = Column(Numeric(precision=10, scale=2))
    status = Column(String, default="outstanding")
    notes = Column(Text, nullable=True)
    
    client = relationship("Client", back_populates="consignations")