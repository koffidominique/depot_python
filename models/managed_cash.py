"""Caisse contrôlée, distincte des sessions historiques non rapprochées."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base
from money import CFAAmount


class ManagedCashSession(Base):
    __tablename__ = 'managed_cash_sessions'
    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False)
    opening_key = Column(String, unique=True, nullable=False)
    closing_key = Column(String, unique=True, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default='open')
    opening_cash = Column(CFAAmount(), nullable=False)
    theoretical_cash = Column(CFAAmount(), nullable=True)
    physical_cash = Column(CFAAmount(), nullable=True)
    difference = Column(CFAAmount(), nullable=True)
    closing_notes = Column(Text, nullable=True)
    entries = relationship('ManagedCashEntry', back_populates='session')
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed')", name='check_managed_cash_status'),
        CheckConstraint('opening_cash >= 0', name='check_managed_opening_cash'),
        Index('uq_managed_cash_open', 'status', unique=True, sqlite_where=(status == 'open')),
    )


class ManagedCashEntry(Base):
    __tablename__ = 'managed_cash_entries'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False, index=True)
    supplier_payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False, unique=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    method = Column(String, nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    session = relationship('ManagedCashSession', back_populates='entries')
    __table_args__ = (CheckConstraint('amount > 0', name='check_managed_cash_entry_positive'),)
