"""Composition explicite des emballages d'un conditionnement commercial."""
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint
from database import Base


class DepositPackagingProfile(Base):
    __tablename__ = 'deposit_packaging_profiles'
    packaging_id = Column(Integer, ForeignKey('product_packagings.id'), primary_key=True)
    mode = Column(String, nullable=False)
    __table_args__ = (CheckConstraint("mode IN ('none','deposit')", name='check_deposit_profile_mode'),)


class DepositPackagingComponent(Base):
    __tablename__ = 'deposit_packaging_components'
    id = Column(Integer, primary_key=True)
    packaging_id = Column(Integer, ForeignKey('deposit_packaging_profiles.packaging_id'), nullable=False, index=True)
    returnable_id = Column(Integer, ForeignKey('returnable_packaging_types.id'), nullable=False)
    pieces_per_pack = Column(Integer, nullable=False)
    __table_args__ = (
        UniqueConstraint('packaging_id', 'returnable_id', name='uq_deposit_packaging_component'),
        CheckConstraint('pieces_per_pack > 0', name='check_deposit_component_pieces'),
    )
