"""Ventes au comptant et mouvements complémentaires de la caisse sécurisée."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from database import Base
from money import CFAAmount


class ManagedSale(Base):
    __tablename__ = 'managed_sales'
    id = Column(Integer, primary_key=True)
    reference = Column(String, nullable=False, unique=True)
    request_key = Column(String, nullable=False, unique=True)
    request_fingerprint = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    mode = Column(String, nullable=False)
    total = Column(CFAAmount(), nullable=False)
    payment_method = Column(String, nullable=False)
    lines = relationship('ManagedSaleLine', back_populates='sale')
    __table_args__ = (CheckConstraint('total > 0', name='check_managed_sale_total'),)


class ManagedSaleLine(Base):
    __tablename__ = 'managed_sale_lines'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('managed_sales.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    packaging_id = Column(Integer, ForeignKey('product_packagings.id'), nullable=False)
    packaging_name = Column(String, nullable=False)
    base_unit = Column(String, nullable=False)
    coefficient = Column(Numeric(10, 3), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    base_quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(CFAAmount(), nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    cost_numerator = Column(String, nullable=True)
    cost_denominator = Column(String, nullable=True)
    sale = relationship('ManagedSale', back_populates='lines')


class ManagedCashTransaction(Base):
    __tablename__ = 'managed_cash_transactions'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('managed_cash_sessions.id'), nullable=False, index=True)
    request_key = Column(String, nullable=False, unique=True)
    sale_id = Column(Integer, ForeignKey('managed_sales.id'), nullable=True, unique=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    kind = Column(String, nullable=False)
    method = Column(String, nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    beneficiary = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    __table_args__ = (
        CheckConstraint("kind IN ('sale', 'expense', 'income', 'outflow', 'correction_in', 'correction_out')", name='check_cash_transaction_kind'),
        CheckConstraint('amount > 0', name='check_cash_transaction_amount'),
        CheckConstraint("(kind = 'sale' AND sale_id IS NOT NULL) OR (kind <> 'sale' AND sale_id IS NULL)", name='check_cash_transaction_sale'),
    )
