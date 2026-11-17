"""Moyens de paiement versionnés : identifiant et libellé historiques immuables."""
from sqlalchemy import Boolean, CheckConstraint, Column, String
from database import Base


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    code = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint('length(code) > 0 AND length(label) > 0', name='check_payment_method_label'),)
