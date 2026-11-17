"""Corrections manuelles traçables, sans coût d'achat fictif."""
from services.packaging_service import quantity
from services.purchase_service import lock_for_write
from services.stock_service import StockService
from models.product import Product


class StockAdjustmentService:
    def __init__(self, db):
        self.db = db

    def adjust(self, product_id, movement_type, amount, reason):
        if movement_type not in ('breakage', 'loss', 'supplier_return', 'customer_return', 'correction_in', 'correction_out'):
            raise ValueError('Type de correction inconnu.')
        reason = str(reason or '').strip()
        if not reason:
            raise ValueError('Le motif est obligatoire.')
        count = quantity(amount)
        delta = count if movement_type in ('customer_return', 'correction_in') else -count
        try:
            lock_for_write(self.db)
            product = self.db.get(Product, product_id)
            if not product or not product.is_active or not product.unit or product.unit == 'unit':
                raise ValueError('Produit actif avec unité de base explicite requis.')
            if product.stock_quantity + delta < 0:
                raise ValueError('La correction ne peut pas rendre le stock négatif.')
            quantity(product.stock_quantity + delta, 'Stock résultant', allow_zero=True)
            if delta > 0:
                product.average_cost_numerator = product.average_cost_denominator = None
            if not StockService(self.db).update_stock(product.id, delta, movement_type,
                                                       unit=product.unit, reason=reason, commit=False):
                raise ValueError('Correction de stock impossible.')
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
