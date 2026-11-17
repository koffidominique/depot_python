"""Créances du nouveau circuit, sans assimilation des anciennes créances."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from database import Base
from money import CFAAmount


class ManagedCreditProfile(Base):
    __tablename__ = 'managed_credit_profiles'
    client_id = Column(Integer, ForeignKey('clients.id'), primary_key=True)
    credit_limit = Column(CFAAmount(), nullable=True)  # NULL : aucun plafond, explicitement choisi
    __table_args__ = (CheckConstraint('credit_limit IS NULL OR credit_limit >= 0', name='check_credit_profile_limit'),)


class ManagedCreditSale(Base):
    __tablename__ = 'managed_credit_sales'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('managed_sales.id'), nullable=False, unique=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    initial_amount = Column(CFAAmount(), nullable=False)
    remaining_amount = Column(CFAAmount(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        CheckConstraint('initial_amount > 0 AND remaining_amount >= 0 AND remaining_amount <= initial_amount', name='check_credit_amounts'),
    )


class ManagedCreditPayment(Base):
    __tablename__ = 'managed_credit_payments'
    id = Column(Integer, primary_key=True)
    credit_sale_id = Column(Integer, ForeignKey('managed_credit_sales.id'), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey('managed_cash_transactions.id'), nullable=False, unique=True)
    request_key = Column(String, nullable=False, unique=True)
    note = Column(Text, nullable=True)
