"""Emballages consignés remis en vente et retours de vides clients."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from database import Base
from money import CFAAmount


class ManagedDepositIssue(Base):
    __tablename__ = 'managed_deposit_issues'
    id = Column(Integer, primary_key=True)
    sale_line_id = Column(Integer, ForeignKey('managed_sale_lines.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    returnable_id = Column(Integer, ForeignKey('returnable_packaging_types.id'), nullable=False)
    pieces = Column(Integer, nullable=False)
    unit_value = Column(CFAAmount(), nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    __table_args__ = (CheckConstraint('pieces > 0 AND unit_value >= 0 AND amount >= 0', name='check_deposit_issue_amount'),)


class ManagedDepositReturn(Base):
    __tablename__ = 'managed_deposit_returns'
    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey('managed_deposit_issues.id'), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False)
    stock_movement_id = Column(Integer, ForeignKey('returnable_stock_movements.id'), nullable=False, unique=True)
    request_key = Column(String, nullable=False, unique=True)
    fingerprint = Column(Text, nullable=False)
    pieces = Column(Integer, nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    credit_reduction = Column(CFAAmount(), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (CheckConstraint('pieces > 0 AND amount >= 0 AND credit_reduction >= 0 AND credit_reduction <= amount', name='check_deposit_return_amount'),)


class ManagedDepositRefund(Base):
    __tablename__ = 'managed_deposit_refunds'
    id = Column(Integer, primary_key=True)
    deposit_return_id = Column(Integer, ForeignKey('managed_deposit_returns.id'), nullable=False, index=True)
    original_transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, index=True)
    refund_transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, unique=True)


class ManagedDepositReturnCancellation(Base):
    __tablename__ = 'managed_deposit_return_cancellations'
    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey('managed_deposit_returns.id'), nullable=False, unique=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False)
    stock_movement_id = Column(Integer, ForeignKey('returnable_stock_movements.id'), nullable=False, unique=True)
    request_key = Column(String, nullable=False, unique=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (CheckConstraint('length(reason) > 0', name='check_deposit_cancellation_reason'),)


class ManagedDepositReturnRecapture(Base):
    __tablename__ = 'managed_deposit_return_recaptures'
    id = Column(Integer, primary_key=True)
    cancellation_id = Column(Integer, ForeignKey('managed_deposit_return_cancellations.id'), nullable=False, index=True)
    refund_id = Column(Integer, ForeignKey('managed_deposit_refunds.id'), nullable=False, unique=True)
    transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, unique=True)
