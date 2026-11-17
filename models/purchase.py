from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    date = Column(DateTime, default=datetime.utcnow)
    order_date = Column(DateTime, nullable=True)
    expected_date = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    received_amount = Column(Numeric(precision=10, scale=2), default=0.0)
    status = Column(String, default="draft")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False)
    
    supplier = relationship("Supplier", back_populates="purchase_orders")
    purchase_order_lines = relationship("PurchaseOrderLine", back_populates="purchase_order")

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    ordered_quantity = Column(Numeric(precision=10, scale=3))
    received_quantity = Column(Numeric(precision=10, scale=3), default=0.0)
    unit_price = Column(Numeric(precision=10, scale=2))
    line_total = Column(Numeric(precision=10, scale=2))
    
    purchase_order = relationship("PurchaseOrder", back_populates="purchase_order_lines")
    product = relationship("Product", back_populates="purchase_order_lines")