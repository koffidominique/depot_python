"""Inventaires physiques : instantané, saisie, puis correction atomique."""
from datetime import datetime
from uuid import uuid4

from models.inventory import Inventory, InventoryLine
from models.product import Product
from models.stock import StockMovement
from services.packaging_service import quantity
from services.purchase_service import lock_for_write
from services.stock_service import StockService


class InventoryService:
    def __init__(self, db):
        self.db = db

    def start(self, product_ids, notes=None):
        if not product_ids or len(set(product_ids)) != len(product_ids):
            raise ValueError('Sélectionnez au moins un produit, sans doublon.')
        try:
            lock_for_write(self.db)
            inventory = Inventory(reference=f'INV-{uuid4().hex.upper()}', notes=(notes or '').strip() or None)
            self.db.add(inventory)
            self.db.flush()
            for product_id in product_ids:
                product = self.db.get(Product, product_id)
                if not product or not product.is_active or not product.unit or product.unit == 'unit':
                    raise ValueError('Produit actif avec unité de base explicite requis.')
                theoretical = quantity(product.stock_quantity, 'Stock théorique', allow_zero=True)
                self.db.add(InventoryLine(inventory_id=inventory.id, product_id=product.id,
                                          theoretical_quantity=theoretical))
            self.db.commit()
            self.db.refresh(inventory)
            return inventory
        except Exception:
            self.db.rollback()
            raise

    def save_counts(self, inventory_id, counts):
        if not counts:
            raise ValueError('Aucun comptage fourni.')
        try:
            lock_for_write(self.db)
            inventory = self.db.get(Inventory, inventory_id)
            if not inventory or inventory.status != 'draft':
                raise ValueError('Inventaire en brouillon introuvable.')
            seen = set()
            for entry in counts:
                line_id = entry.get('line_id')
                if line_id in seen:
                    raise ValueError('Ligne de comptage répétée.')
                seen.add(line_id)
                line = self.db.get(InventoryLine, line_id)
                if not line or line.inventory_id != inventory.id:
                    raise ValueError('Ligne d’inventaire introuvable.')
                line.counted_quantity = quantity(entry.get('counted_quantity'), 'Stock physique', allow_zero=True)
                line.reason = str(entry.get('reason') or '').strip() or None
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def validate(self, inventory_id, user_id=None):
        try:
            lock_for_write(self.db)
            inventory = self.db.get(Inventory, inventory_id)
            if not inventory or inventory.status != 'draft':
                raise ValueError('Seul un inventaire en brouillon peut être validé.')
            if not inventory.lines:
                raise ValueError('Inventaire vide.')
            # Vérifier toutes les lignes avant tout mouvement ; une modification
            # entre le comptage et la validation impose un nouvel inventaire.
            for line in inventory.lines:
                product = line.product
                if line.counted_quantity is None:
                    raise ValueError('Tous les stocks physiques doivent être renseignés.')
                if not product.is_active or not product.unit or product.unit == 'unit':
                    raise ValueError('Produit inactif ou sans unité de base explicite.')
                moved = self.db.query(StockMovement.id).filter(StockMovement.product_id == product.id,
                    StockMovement.date >= inventory.created_at).first()
                if moved or product.stock_quantity != line.theoretical_quantity:
                    raise ValueError('Le stock a changé depuis le début de l’inventaire ; recommencez.')
                if line.counted_quantity != line.theoretical_quantity and not (line.reason or '').strip():
                    raise ValueError('Un motif est obligatoire pour chaque écart.')
            stock = StockService(self.db)
            for line in inventory.lines:
                delta = line.counted_quantity - line.theoretical_quantity
                if not delta:
                    continue
                # Les unités supplémentaires ont un coût inconnu : ne pas leur
                # attribuer fictivement le coût des unités déjà présentes.
                if delta > 0:
                    line.product.average_cost_numerator = None
                    line.product.average_cost_denominator = None
                if not stock.update_stock(line.product_id, delta, 'inventory_adjustment', unit=line.product.unit,
                                          user_id=user_id, reason=line.reason,
                                          reference_document=inventory.reference, commit=False):
                    raise ValueError('Impossible de régulariser le stock.')
            inventory.status = 'validated'
            inventory.validated_at = datetime.utcnow()
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def cancel(self, inventory_id):
        try:
            lock_for_write(self.db)
            inventory = self.db.get(Inventory, inventory_id)
            if not inventory or inventory.status != 'draft':
                raise ValueError('Seul un inventaire en brouillon peut être annulé.')
            inventory.status = 'cancelled'
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
