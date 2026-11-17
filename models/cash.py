from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class CashSession(Base):
    __tablename__ = "cash_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    opening_date = Column(DateTime, default=datetime.utcnow)
    closing_date = Column(DateTime, nullable=True)
    initial_cash = Column(Numeric(precision=10, scale=2), default=0.0)
    total_cash_sales = Column(Numeric(precision=10, scale=2), default=0.0)
    total_mobile_money = Column(Numeric(precision=10, scale=2), default=0.0)
    total_transfers = Column(Numeric(precision=10, scale=2), default=0.0)
    total_other = Column(Numeric(precision=10, scale=2), default=0.0)
    total_expenses = Column(Numeric(precision=10, scale=2), default=0.0)
    theoretical_balance = Column(Numeric(precision=10, scale=2), default=0.0)
    physical_balance = Column(Numeric(precision=10, scale=2), nullable=True)
    difference = Column(Numeric(precision=10, scale=2), nullable=True)
    status = Column(String, default="open")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    closing_notes = Column(Text, nullable=True)
    
    cash_movements = relationship("CashMovement", back_populates="cash_session")

class CashMovement(Base):
    __tablename__ = "cash_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"))
    date = Column(DateTime, default=datetime.utcnow)
    movement_type = Column(String)
    amount = Column(Numeric(precision=10, scale=2))
    payment_method = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    cash_session = relationship("CashSession", back_populates="cash_movements")