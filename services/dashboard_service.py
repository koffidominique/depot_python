"""Indicateurs lus dans SQLite, sans rapprochement implicite des historiques."""
from sqlalchemy import func
from models.client import Client
from models.product import Product
from models.managed_credit import ManagedCreditSale
from models.managed_operations import ManagedSale, ManagedSaleCancellation
from services.managed_cash_service import ManagedCashService
from money import fcfa


class DashboardService:
    def __init__(self, db):
        self.db = db

    def snapshot(self):
        cash = ManagedCashService(self.db)
        session = cash.get_open()
        return {
            'active_products': self.db.query(Product).filter(Product.is_active.is_(True)).count(),
            'low_stock': self.db.query(Product).filter(
                Product.is_active.is_(True), Product.min_stock > 0,
                Product.stock_quantity <= Product.min_stock).count(),
            'active_clients': self.db.query(Client).filter(Client.is_active.is_(True)).count(),
            'managed_sales': self.db.query(ManagedSale).outerjoin(
                ManagedSaleCancellation, ManagedSaleCancellation.sale_id == ManagedSale.id).filter(
                ManagedSaleCancellation.id.is_(None)).count(),
            'managed_credit': fcfa(self.db.query(func.coalesce(func.sum(ManagedCreditSale.remaining_amount), 0)).scalar(), 'Créances du nouveau circuit'),
            'cash_reference': session.reference if session else None,
            'cash_theoretical': cash.cash_available(session) if session else None,
        }
