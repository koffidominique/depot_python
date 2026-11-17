from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Numeric, CheckConstraint, Index
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="category")
    
    __table_args__ = (
        CheckConstraint('LENGTH(name) > 0', name='check_category_name_not_empty'),
    )

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    barcode = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    brand = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    description = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    packaging = Column(String, default="unit")
    unit = Column(String, default="unit")
    purchase_price = Column(Numeric(precision=10, scale=2), default=0.0)
    wholesale_price = Column(Numeric(precision=10, scale=2), default=0.0)
    semi_wholesale_price = Column(Numeric(precision=10, scale=2), default=0.0)
    retail_price = Column(Numeric(precision=10, scale=2), default=0.0)
    stock_quantity = Column(Numeric(precision=10, scale=3), default=0.0)
    min_stock = Column(Numeric(precision=10, scale=3), default=0.0)
    max_stock = Column(Numeric(precision=10, scale=3), default=0.0)
    consignment_value = Column(Numeric(precision=10, scale=2), default=0.0)
    image_path = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    sale_lines = relationship("SaleLine", back_populates="product")
    purchase_order_lines = relationship("PurchaseOrderLine", back_populates="product")
    consignation_lines = relationship("ConsignationLine", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    __table_args__ = (
        CheckConstraint('LENGTH(reference) > 0', name='check_product_reference_not_empty'),
        CheckConstraint('LENGTH(name) > 0', name='check_product_name_not_empty'),
        CheckConstraint('purchase_price >= 0', name='check_purchase_price_positive'),
        CheckConstraint('wholesale_price >= 0', name='check_wholesale_price_positive'),
        CheckConstraint('semi_wholesale_price >= 0', name='check_semi_wholesale_price_positive'),
        CheckConstraint('retail_price >= 0', name='check_retail_price_positive'),
        CheckConstraint('min_stock >= 0', name='check_min_stock_positive'),
        CheckConstraint('max_stock >= 0', name='check_max_stock_positive'),
        Index('idx_product_category', 'category_id'),
        Index('idx_product_supplier', 'supplier_id'),
        Index('idx_product_active', 'is_active'),
    )