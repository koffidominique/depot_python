from money import CFAAmount
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Numeric, DateTime, Boolean, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    order_date = Column(DateTime, nullable=True)
    expected_date = Column(DateTime, nullable=True)
    total_amount = Column(CFAAmount(), default=0.0)
    received_amount = Column(CFAAmount(), default=0.0)
    status = Column(String, default="draft")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    supplier = relationship("Supplier", back_populates="purchase_orders")
    purchase_order_lines = relationship("PurchaseOrderLine", back_populates="purchase_order")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_purchase_reference_not_empty'),
        CheckConstraint('total_amount >= 0', name='check_purchase_total_amount_positive'),
        CheckConstraint('received_amount >= 0', name='check_purchase_received_amount_positive'),
        Index('idx_purchase_supplier', 'supplier_id'),
        Index('idx_purchase_date', 'date'),
        Index('idx_purchase_status', 'status'),
    )

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    ordered_quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    received_quantity = Column(Numeric(precision=10, scale=3), default=0.0)
    # Instantané, inchangé si le conditionnement est modifié plus tard.
    packaging_id = Column(Integer, ForeignKey('product_packagings.id'), nullable=True)
    packaging_name = Column(String, nullable=True)
    base_unit = Column(String, nullable=True)
    conversion_factor = Column(Numeric(10, 3), nullable=True)
    allow_fraction = Column(Boolean, nullable=True)
    unit_price = Column(CFAAmount(), nullable=False)
    unit_discount = Column(CFAAmount(), nullable=True)
    unit_fee = Column(CFAAmount(), nullable=True)
    line_total = Column(CFAAmount(), nullable=False)
    
    purchase_order = relationship("PurchaseOrder", back_populates="purchase_order_lines")
    product = relationship("Product", back_populates="purchase_order_lines")
    
    __table_args__ = (
        CheckConstraint('ordered_quantity > 0', name='check_purchase_line_ordered_quantity_positive'),
        CheckConstraint('received_quantity >= 0', name='check_purchase_line_received_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_purchase_line_unit_price_positive'),
        CheckConstraint('line_total >= 0', name='check_purchase_line_total_positive'),
        Index('idx_purchase_line_order', 'purchase_order_id'),
        Index('idx_purchase_line_product', 'product_id'),
    )