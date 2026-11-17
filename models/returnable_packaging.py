"""Catalogue des emballages physiques ; distinct des conditionnements commerciaux."""
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from database import Base
from money import CFAAmount


class ReturnablePackagingType(Base):
    __tablename__ = 'returnable_packaging_types'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    producer = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    description = Column(String, nullable=True)
    deposit_value = Column(CFAAmount(), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("kind IN ('bottle', 'crate')", name='check_returnable_packaging_kind'),
        CheckConstraint('length(code) > 0 AND length(name) > 0 AND length(producer) > 0', name='check_returnable_packaging_label'),
        CheckConstraint('deposit_value IS NULL OR deposit_value >= 0', name='check_returnable_packaging_deposit'),
    )
