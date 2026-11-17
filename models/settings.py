from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from database import Base

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, default="DEPOTPRO")
    company_legal_name = Column(String, nullable=True)
    logo_path = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    currency = Column(String, default="FCFA")
    tax_rate = Column(Float, default=0.0)
    price_display = Column(String, default="HT")
    decimal_separator = Column(String, default=".")
    thousands_separator = Column(String, default=",")
    invoice_prefix = Column(String, default="FAC")
    sale_prefix = Column(String, default="VTE")
    purchase_prefix = Column(String, default="ACH")
    order_prefix = Column(String, default="CMD")
    delivery_prefix = Column(String, default="BL")
    receipt_prefix = Column(String, default="REC")
    auto_backup = Column(Boolean, default=True)
    backup_frequency = Column(String, default="daily")
    theme = Column(String, default="light")
    primary_color = Column(String, default="#2563eb")