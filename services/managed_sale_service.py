"""Vente au comptant, encaissée intégralement en un moyen, atomique avec stock et caisse."""
import json
from uuid import uuid4
from models.managed_cash import ManagedCashSession
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedCashTransaction
from models.packaging import ProductPackaging
from money import fcfa
from services.cash_methods import METHODS
from services.managed_cash_service import ManagedCashService, _key
from services.packaging_service import quantity
from services.purchase_service import lock_for_write
from services.stock_service import StockService


class ManagedSaleService:
    PRICE_FIELDS = {'retail': 'retail_price', 'wholesale': 'wholesale_price', 'semi_wholesale': 'semi_wholesale_price'}

    def __init__(self, db):
        self.db = db

    def sell(self, session_id, mode, method, lines, request_key):
        key = _key(request_key)
        if mode not in self.PRICE_FIELDS or method not in METHODS:
            raise ValueError('Tarif ou moyen de paiement invalide.')
        if not lines:
            raise ValueError('Le panier doit contenir au moins une ligne.')
        normalized = []
        for line in lines:
            package_id = line.get('packaging_id')
            if not isinstance(package_id, int) or isinstance(package_id, bool):
                raise ValueError('Conditionnement invalide.')
            count = quantity(line.get('quantity'), 'Quantité vendue')
            expected = line.get('expected_unit_price')
            expected = None if expected is None else fcfa(expected, 'Prix attendu')
            normalized.append((package_id, str(count.normalize()), expected))
        fingerprint = json.dumps([session_id, mode, method, normalized], ensure_ascii=False, separators=(',', ':'))
        try:
            lock_for_write(self.db)
            previous = self.db.query(ManagedSale).filter_by(request_key=key).first()
            if previous:
                if previous.request_fingerprint == fingerprint:
                    ident = previous.id
                    self.db.rollback()
                    return self.db.get(ManagedSale, ident)
                raise ValueError('Cette clé de vente a déjà été utilisée.')
            session = self.db.get(ManagedCashSession, session_id)
            if not session or session.status != 'open':
                raise ValueError('Une caisse ouverte est obligatoire.')
            sale = ManagedSale(reference=f'VENTE-{uuid4().hex.upper()}', request_key=key,
                request_fingerprint=fingerprint, mode=mode, total=1, payment_method=method)
            self.db.add(sale)
            self.db.flush()
            total = 0
            for package_id, count_text, expected_price in normalized:
                pack = self.db.get(ProductPackaging, package_id)
                if not pack or not pack.is_active or not pack.product.is_active:
                    raise ValueError('Conditionnement ou produit actif introuvable.')
                product = pack.product
                if product.consignment_value is not None and product.consignment_value > 0:
                    raise ValueError('La consigne de ce produit n’est pas encore prise en charge par cette vente.')
                if not pack.base_unit or pack.base_unit == 'unit' or pack.base_unit != product.unit:
                    raise ValueError('Unité de base du conditionnement incohérente.')
                count = quantity(count_text)
                if not pack.allow_fraction and count != count.to_integral_value():
                    raise ValueError('Ce conditionnement exige une quantité entière.')
                base_quantity = quantity(count * pack.coefficient, 'Quantité de base vendue')
                if product.stock_quantity is None or product.stock_quantity < base_quantity:
                    raise ValueError(f'Stock insuffisant pour {product.name}.')
                price = getattr(pack, self.PRICE_FIELDS[mode])
                if price is None:
                    raise ValueError(f'Tarif non configuré pour {product.name} : {pack.name}.')
                if price < 0:
                    raise ValueError('Tarif négatif invalide.')
                _ = product.average_cost  # refuse un coût historique corrompu

                if expected_price is not None and price != expected_price:
                    raise ValueError('Le tarif a changé depuis l’aperçu ; vérifiez à nouveau le panier.')
                amount = fcfa(count * price, 'Total de ligne')
                total = fcfa(total + amount, 'Total vente')
                self.db.add(ManagedSaleLine(sale_id=sale.id, product_id=product.id, packaging_id=pack.id,
                    packaging_name=pack.name, base_unit=pack.base_unit, coefficient=pack.coefficient,
                    quantity=count, base_quantity=base_quantity, unit_price=price, amount=amount,
                    cost_numerator=product.average_cost_numerator, cost_denominator=product.average_cost_denominator))
                if not StockService(self.db).update_stock(product.id, -base_quantity, 'sale', unit=product.unit,
                                                           reference_document=sale.reference, commit=False):
                    raise ValueError('Mise à jour du stock impossible.')
            if total <= 0:
                raise ValueError('Le total de la vente doit être positif.')
            if method == 'cash':
                fcfa(ManagedCashService(self.db).cash_available(session) + total, 'Espèces théoriques')
            sale.total = total
            self.db.add(ManagedCashTransaction(session_id=session.id, request_key=f'vente:{key}', sale_id=sale.id,
                kind='sale', method=method, amount=total, description=f'Vente {sale.reference}', reference=sale.reference))
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise
