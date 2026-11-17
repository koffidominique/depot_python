from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from money import CFAAmount


class PurchaseReceipt(Base):
    __tablename__ = 'purchase_receipts'
    id = Column(Integer, primary_key=True)
    reference = Column(String, nullable=False, unique=True)
    request_key = Column(String, nullable=False, unique=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_amount = Column(CFAAmount(), nullable=False)
    lines = relationship('PurchaseReceiptLine', back_populates='receipt')


class PurchaseReceiptLine(Base):
    __tablename__ = 'purchase_receipt_lines'
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer, ForeignKey('purchase_receipts.id'), nullable=False, index=True)
    purchase_order_line_id = Column(Integer, ForeignKey('purchase_order_lines.id'), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    base_quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(CFAAmount(), nullable=False)
    amount = Column(CFAAmount(), nullable=False)
    receipt = relationship('PurchaseReceipt', back_populates='lines')
    __table_args__ = (UniqueConstraint('receipt_id', 'purchase_order_line_id', name='uq_receipt_order_line'),)
