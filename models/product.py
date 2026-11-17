from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, index=True)
    brand = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
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
    stock_movements = relationship("StockMovement", back_populates="product")