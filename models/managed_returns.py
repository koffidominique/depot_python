"""Retours partiels et contreparties, sans effacer les écritures d'origine."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from database import Base
from money import CFAAmount


class ManagedReturn(Base):
    __tablename__ = 'managed_returns'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('managed_sales.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False)
    request_key = Column(String, nullable=False, unique=True)
    fingerprint = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    total = Column(CFAAmount(), nullable=False)
    credit_reduction = Column(CFAAmount(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (CheckConstraint('total >= 0 AND credit_reduction >= 0 AND credit_reduction <= total', name='check_return_total'),)


class ManagedReturnLine(Base):
    __tablename__ = 'managed_return_lines'
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('managed_returns.id'), nullable=False, index=True)
    sale_line_id = Column(Integer, ForeignKey('managed_sale_lines.id'), nullable=False, index=True)
    base_quantity = Column(Numeric(10, 3), nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    __table_args__ = (CheckConstraint('base_quantity > 0 AND amount >= 0', name='check_return_line'),)


class ManagedReturnRefund(Base):
    __tablename__ = 'managed_return_refunds'
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('managed_returns.id'), nullable=False, index=True)
    original_transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, index=True)
    refund_transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, unique=True)


class ManagedReturnCancellation(Base):
    __tablename__ = 'managed_return_cancellations'
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('managed_returns.id'), nullable=False, unique=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False)
    request_key = Column(String, nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (CheckConstraint('length(reason) > 0', name='check_return_cancellation_reason'),)


class ManagedReturnRecapture(Base):
    __tablename__ = 'managed_return_recaptures'
    id = Column(Integer, primary_key=True)
    cancellation_id = Column(Integer, ForeignKey('managed_return_cancellations.id'), nullable=False, index=True)
    refund_id = Column(Integer, ForeignKey('managed_return_refunds.id'), nullable=False, unique=True)
    transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, unique=True)
