"""Ventes au comptant, encaissement en un ou plusieurs moyens, stock et caisse atomiques."""
import json
from uuid import uuid4
from models.managed_cash import ManagedCashSession
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedCashTransaction, ManagedSalePayment
from models.packaging import ProductPackaging
from models.managed_credit import ManagedCreditSale
from models.managed_deposit import ManagedDepositIssue
from models.client import Client
from services.managed_credit_service import eligible_client
from services.deposit_configuration_service import DepositConfigurationService
from sqlalchemy import func
from money import fcfa
from services.cash_methods import require_active
from services.managed_cash_service import ManagedCashService, _key
from services.packaging_service import quantity
from services.purchase_service import lock_for_write
from services.stock_service import StockService


class ManagedSaleService:
    PRICE_FIELDS = {'retail': 'retail_price', 'wholesale': 'wholesale_price', 'semi_wholesale': 'semi_wholesale_price'}

    def __init__(self, db):
        self.db = db

    def sell(self, session_id, mode, method, lines, request_key, *, payments=None, client_id=None, override_limit=False):
        key = _key(request_key)
        if mode not in self.PRICE_FIELDS:
            raise ValueError('Tarif ou moyen de paiement invalide.')
        is_credit = method == 'credit'
        if is_credit and (not isinstance(client_id, int) or isinstance(client_id, bool)):
            raise ValueError('Une vente à crédit exige un client identifié.')
        if not is_credit and override_limit is not False:
            raise ValueError('Le dépassement de plafond est réservé au crédit.')
        if client_id is not None and (not isinstance(client_id, int) or isinstance(client_id, bool)):
            raise ValueError('Client invalide.')
        if override_limit is not False and override_limit is not True:
            raise ValueError('Confirmation de plafond invalide.')
        split = None
        if payments is None:
            if not isinstance(method, str) or method in ('mixed', 'credit'):
                raise ValueError('Tarif ou moyen de paiement invalide.')
        else:
            if (method not in ('mixed', 'credit') or not isinstance(payments, (list, tuple))
                    or len(payments) > 100 or (method == 'mixed' and len(payments) < 2)):
                raise ValueError('Indiquez des moyens de paiement distincts et valides.')
            split = []
            seen = set()
            for payment in payments:
                if not isinstance(payment, dict) or not isinstance(payment.get('method'), str):
                    raise ValueError('Moyen de paiement invalide.')
                payment_method = payment['method']
                if payment_method in seen:
                    raise ValueError('Chaque moyen doit être indiqué une seule fois.')
                seen.add(payment_method)
                amount = fcfa(payment.get('amount'), 'Montant encaissé')
                if amount <= 0:
                    raise ValueError('Chaque montant encaissé doit être positif.')
                split.append((payment_method, amount))
            split.sort()
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
            override = line.get('unit_price')
            override = None if override is None else fcfa(override, 'Prix de vente')
            if override is not None and override < 0:
                raise ValueError('Le prix de vente ne peut pas être négatif.')
            if override is not None and expected is None:
                raise ValueError('Vérifiez le tarif configuré avant de modifier le prix.')
            # Garder l'empreinte précédente pour les ventes sans prix modifié.
            item = (package_id, str(count.normalize()), expected)
            deposits = line.get('expected_deposits')
            if deposits is not None:
                if not isinstance(deposits, list) or not deposits or len(deposits) > 100:
                    raise ValueError('Aperçu de consigne invalide.')
                try:
                    serialized = json.dumps(deposits, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                except (TypeError, ValueError):
                    raise ValueError('Aperçu de consigne invalide.') from None
                if len(serialized) > 30000:
                    raise ValueError('Aperçu de consigne trop long.')
                normalized.append((*item, override, serialized))
            else:
                normalized.append(item if override is None else (*item, override))
        payload = [session_id, mode, method, normalized]
        if split is not None:
            payload.append(split)
        if is_credit:
            payload.extend((client_id, override_limit))
        elif client_id is not None:
            payload.append({'deposit_client': client_id})
        fingerprint = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        try:
            lock_for_write(self.db)
            previous = self.db.query(ManagedSale).filter_by(request_key=key).first()
            if previous:
                if previous.request_fingerprint == fingerprint:
                    ident = previous.id
                    self.db.rollback()
                    return self.db.get(ManagedSale, ident)
                raise ValueError('Cette clé de vente a déjà été utilisée.')
            for code in ([method] if split is None else [code for code, _ in split]):
                require_active(self.db, code)
            session = self.db.get(ManagedCashSession, session_id)
            if not session or session.status != 'open':
                raise ValueError('Une caisse ouverte est obligatoire.')
            sale = ManagedSale(reference=f'VENTE-{uuid4().hex.upper()}', request_key=key,
                request_fingerprint=fingerprint, mode=mode, total=1, payment_method=method)
            self.db.add(sale)
            self.db.flush()
            total = 0
            has_deposit = False
            for item in normalized:
                package_id, count_text, expected_price = item[:3]
                override_price = item[3] if len(item) >= 4 else None
                expected_deposits = item[4] if len(item) == 5 else None
                pack = self.db.get(ProductPackaging, package_id)
                if not pack or not pack.is_active or not pack.product.is_active:
                    raise ValueError('Conditionnement ou produit actif introuvable.')
                product = pack.product
                if product.consignment_value is not None and product.consignment_value > 0:
                    raise ValueError('La consigne de ce produit n’est pas encore prise en charge par cette vente.')
                if not pack.base_unit or pack.base_unit == 'unit' or pack.base_unit != product.unit:
                    raise ValueError('Unité de base du conditionnement incohérente.')
                count = quantity(count_text)
                deposit_components = DepositConfigurationService(self.db).quote(pack.id, count)
                if deposit_components:
                    if expected_deposits is None:
                        raise ValueError('Vérifiez les consignes dans l’aperçu avant de vendre.')
                    snapshot = json.dumps(deposit_components, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                    if snapshot != expected_deposits:
                        raise ValueError('La consigne a changé depuis l’aperçu ; vérifiez à nouveau la vente.')
                    client = self.db.get(Client, client_id) if client_id is not None else None
                    if not client or not client.is_active:
                        raise ValueError('Un client actif est obligatoire pour les emballages consignés.')
                    has_deposit = True
                elif expected_deposits is not None:
                    raise ValueError('La consigne a changé depuis l’aperçu ; vérifiez à nouveau la vente.')
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
                price = price if override_price is None else override_price
                amount = fcfa(count * price, 'Total de ligne')
                total = fcfa(total + amount, 'Total vente')
                sale_line = ManagedSaleLine(sale_id=sale.id, product_id=product.id, packaging_id=pack.id,
                    packaging_name=pack.name, base_unit=pack.base_unit, coefficient=pack.coefficient,
                    quantity=count, base_quantity=base_quantity, unit_price=price, amount=amount,
                    cost_numerator=product.average_cost_numerator, cost_denominator=product.average_cost_denominator)
                self.db.add(sale_line)
                self.db.flush()
                for component in deposit_components:
                    total = fcfa(total + component['amount'], 'Total vente avec consigne')
                    self.db.add(ManagedDepositIssue(sale_line_id=sale_line.id, client_id=client_id,
                        returnable_id=component['returnable_id'], pieces=component['pieces'],
                        unit_value=component['unit_value'], amount=component['amount']))
                if not StockService(self.db).update_stock(product.id, -base_quantity, 'sale', unit=product.unit,
                                                           reference_document=sale.reference, commit=False):
                    raise ValueError('Mise à jour du stock impossible.')
            if not is_credit and client_id is not None and not has_deposit:
                raise ValueError('Aucun emballage consigné dans cette vente ; ne sélectionnez pas de client ici.')
            if total <= 0:
                raise ValueError('Le total de la vente doit être positif.')
            paid = fcfa(sum(amount for _, amount in split), 'Total encaissé') if split is not None else total
            if is_credit:
                if paid >= total:
                    raise ValueError('Pour une vente à crédit, le solde restant doit être positif et aucun trop-perçu n’est autorisé.')
                client, profile = eligible_client(self.db, client_id)
                current = fcfa(self.db.query(func.coalesce(func.sum(ManagedCreditSale.remaining_amount), 0)).filter_by(client_id=client.id).scalar(), 'Créances client')
                due = fcfa(total - paid, 'Reste à payer')
                total_due = fcfa(current + due, 'Créances client')
                if profile.credit_limit is not None and total_due > profile.credit_limit and not override_limit:
                    raise ValueError('Plafond de crédit dépassé : confirmation explicite obligatoire.')
                self.db.add(ManagedCreditSale(sale_id=sale.id, client_id=client.id, initial_amount=due, remaining_amount=due))
            elif split is not None and paid != total:
                raise ValueError('La somme des paiements doit correspondre exactement au total de vente.')
            cash_amount = total if split is None and method == 'cash' else sum(amount for m, amount in (split or []) if m == 'cash')
            if cash_amount:
                fcfa(ManagedCashService(self.db).cash_available(session) + cash_amount, 'Espèces théoriques')
            sale.total = total
            if split is None:
                self.db.add(ManagedCashTransaction(session_id=session.id, request_key=f'vente:{key}', sale_id=sale.id,
                    kind='sale', method=method, amount=total, description=f'Vente {sale.reference}', reference=sale.reference))
            else:
                for index, (payment_method, amount) in enumerate(split):
                    # Le modèle historique autorise un seul mouvement portant sale_id.
                    # Chaque mouvement, y compris les autres entrées, est relié par FK ci-dessous.
                    movement = ManagedCashTransaction(session_id=session.id, request_key=f'vente-mixte:{key}:{index}',
                        sale_id=sale.id if index == 0 else None, kind='sale' if index == 0 else 'income',
                        method=payment_method, amount=amount, description=f'Paiement vente {sale.reference}', reference=sale.reference)
                    self.db.add(movement)
                    self.db.flush()
                    self.db.add(ManagedSalePayment(sale_id=sale.id, transaction_id=movement.id))
            self.db.commit()
            self.db.refresh(sale)
            return sale
        except Exception:
            self.db.rollback()
            raise
