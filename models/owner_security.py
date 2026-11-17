from sqlalchemy import CheckConstraint, Column, Integer, String
from database import Base


class OwnerSecurity(Base):
    """Configuration locale unique ; aucune identité commerciale n'est supprimée."""
    __tablename__ = 'owner_security'

    id = Column(Integer, primary_key=True)
    pin_hash = Column(String, nullable=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(Integer, nullable=False, default=0)
    inactivity_seconds = Column(Integer, nullable=False, default=900)
    __table_args__ = (CheckConstraint('id = 1', name='owner_security_singleton'),)
