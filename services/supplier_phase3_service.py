"""Création minimale d'un fournisseur sans toucher aux soldes historiques."""
from uuid import uuid4
from models.supplier import Supplier
from services.purchase_service import lock_for_write


class SupplierPhase3Service:
    def __init__(self, db):
        self.db = db

    def create(self, name, phone):
        name, phone = str(name or '').strip(), str(phone or '').strip()
        if not name or not phone or len(name) > 200 or len(phone) > 50:
            raise ValueError('Nom et téléphone fournisseur valides requis.')
        try:
            lock_for_write(self.db)
            supplier = Supplier(code=f'FOUR-{uuid4().hex.upper()}', name=name, phone=phone,
                                balance_due=0, total_purchases=0, is_active=True)
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            return supplier
        except Exception:
            self.db.rollback()
            raise
