"""Stock de vides déclaré séparément des stocks de boissons."""
from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class ReturnableStockBalance(Base):
    __tablename__ = 'returnable_stock_balances'
    packaging_id = Column(Integer, ForeignKey('returnable_packaging_types.id'), primary_key=True)
    quantity = Column(Integer, nullable=False)
    packaging = relationship('ReturnablePackagingType')
    __table_args__ = (CheckConstraint('quantity >= 0', name='check_returnable_balance_nonnegative'),)


class ReturnableStockMovement(Base):
    __tablename__ = 'returnable_stock_movements'
    id = Column(Integer, primary_key=True)
    request_key = Column(String, nullable=False, unique=True)
    packaging_id = Column(Integer, ForeignKey('returnable_packaging_types.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    movement_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    stock_before = Column(Integer, nullable=True)  # inconnu avant le premier comptage
    stock_after = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    reference_document = Column(String, nullable=True)
    packaging = relationship('ReturnablePackagingType')
    __table_args__ = (
        CheckConstraint("movement_type IN ('initial', 'entry', 'exit', 'breakage', 'loss', 'correction_in', 'correction_out')", name='check_returnable_movement_type'),
        CheckConstraint('stock_after >= 0 AND (stock_before IS NULL OR stock_before >= 0)', name='check_returnable_movement_balances'),
    )
