from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Inventory(Base):
    __tablename__ = 'inventories'
    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default='draft')
    notes = Column(Text, nullable=True)
    lines = relationship('InventoryLine', back_populates='inventory')
    __table_args__ = (CheckConstraint("status IN ('draft', 'validated', 'cancelled')", name='check_inventory_status'),)


class InventoryLine(Base):
    __tablename__ = 'inventory_lines'
    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventories.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    theoretical_quantity = Column(Numeric(10, 3), nullable=False)
    counted_quantity = Column(Numeric(10, 3), nullable=True)
    reason = Column(Text, nullable=True)
    inventory = relationship('Inventory', back_populates='lines')
    product = relationship('Product')
    __table_args__ = (
        UniqueConstraint('inventory_id', 'product_id', name='uq_inventory_product'),
        CheckConstraint('counted_quantity IS NULL OR counted_quantity >= 0', name='check_inventory_count_positive'),
    )
