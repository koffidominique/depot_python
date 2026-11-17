from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    date = Column(DateTime, default=datetime.utcnow)
    movement_type = Column(String)
    quantity = Column(Numeric(precision=10, scale=3))
    unit = Column(String)
    stock_before = Column(Numeric(precision=10, scale=3))
    stock_after = Column(Numeric(precision=10, scale=3))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    reference_document = Column(String, nullable=True)
    
    product = relationship("Product", back_populates="stock_movements")