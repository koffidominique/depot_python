from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    category = Column(String)
    amount = Column(Numeric(precision=10, scale=2))
    payment_method = Column(String)
    beneficiary = Column(String, nullable=True)
    receipt_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_paid = Column(String, default="cash")