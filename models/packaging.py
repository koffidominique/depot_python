from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from money import CFAAmount


class ProductPackaging(Base):
    __tablename__ = 'product_packagings'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    base_unit = Column(String, nullable=False)
    coefficient = Column(Numeric(10, 3), nullable=False)
    purchase_price = Column(CFAAmount(), nullable=True)
    wholesale_price = Column(CFAAmount(), nullable=True)
    retail_price = Column(CFAAmount(), nullable=True)
    semi_wholesale_price = Column(CFAAmount(), nullable=True)
    barcode = Column(String, unique=True, nullable=True)
    allow_fraction = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    product = relationship('Product', back_populates='packagings')

    __table_args__ = (
        UniqueConstraint('product_id', 'name', name='uq_packaging_product_name'),
        CheckConstraint("name IN ('casier','carton','bouteille','pack','canette')", name='check_packaging_name'),
        CheckConstraint('coefficient > 0', name='check_packaging_coefficient'),
        CheckConstraint('purchase_price IS NULL OR purchase_price >= 0', name='check_packaging_purchase_price'),
        CheckConstraint('wholesale_price IS NULL OR wholesale_price >= 0', name='check_packaging_wholesale_price'),
        CheckConstraint('retail_price IS NULL OR retail_price >= 0', name='check_packaging_retail_price'),
        CheckConstraint('semi_wholesale_price IS NULL OR semi_wholesale_price >= 0', name='check_packaging_semi_wholesale_price'),
    )
