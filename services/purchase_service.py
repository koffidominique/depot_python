"""Commandes et réceptions de marchandises ; paiements fournisseurs non intégrés."""
from fractions import Fraction
from uuid import uuid4
from models.purchase import PurchaseOrder, PurchaseOrderLine
from models.product import Product
from models.supplier import Supplier
from models.packaging import ProductPackaging
from models.reception import PurchaseReceipt, PurchaseReceiptLine
from models.debt import SupplierDebt
from models.payment import Payment
from money import fcfa
from services.packaging_service import quantity
from services.stock_service import StockService
from validation import validate_price, validate_date, validate_reference
from services.sqlite_transaction import lock_for_write



class PurchaseService:
    def __init__(self, db):
        self.db = db
        self.stock_service = StockService(db)

    def get_all_purchase_orders(self, include_cancelled=False):
        query = self.db.query(PurchaseOrder)
        if not include_cancelled:
            query = query.filter(PurchaseOrder.is_cancelled.is_(False))
        return query.order_by(PurchaseOrder.date.desc(), PurchaseOrder.id.desc()).all()

    def get_purchase_order_by_id(self, order_id):
        return self.db.get(PurchaseOrder, order_id)

    def create_purchase_order(self, order_data, order_lines_data, user_id=None):
        if not order_lines_data:
            raise ValueError('La commande doit comporter au moins une ligne.')
        try:
            lock_for_write(self.db)
            supplier = self.db.get(Supplier, order_data.get('supplier_id'))
            if not supplier or not supplier.is_active:
                raise ValueError('Fournisseur actif introuvable.')
            reference = validate_reference((str(order_data.get('reference') or '').strip() or f'CMD-{uuid4().hex.upper()}'), 'Référence')
            if self.db.query(PurchaseOrder.id).filter_by(reference=reference).first():
                raise ValueError('Cette référence de commande existe déjà.')
            order = PurchaseOrder(reference=reference, supplier_id=supplier.id,
                                  order_date=validate_date(order_data.get('order_date') or None, 'Date commande'),
                                  expected_date=validate_date(order_data.get('expected_date') or None, 'Date prévue'),
                                  notes=order_data.get('notes'), status='draft', user_id=user_id)
            self.db.add(order)
            self.db.flush()
            total = 0
            for line in order_lines_data:
                item = self.db.get(ProductPackaging, line.get('packaging_id'))
                if not item or not item.is_active or not item.product.is_active:
                    raise ValueError('Conditionnement actif introuvable.')
                if item.base_unit != item.product.unit or not item.base_unit or item.base_unit == 'unit':
                    raise ValueError('Unité de base du conditionnement incompatible avec le produit.')
                if line.get('product_id') is not None and item.product_id != line['product_id']:
                    raise ValueError('Le conditionnement ne correspond pas au produit.')
                count = quantity(line.get('ordered_quantity'), 'Quantité commandée')
                if not item.allow_fraction and count != count.to_integral_value():
                    raise ValueError('Ce conditionnement exige une quantité entière.')
                quantity(count * item.coefficient, 'Quantité de base')
                price = validate_price(line.get('unit_price'), 'Prix achat')
                discount = validate_price(line.get('unit_discount', 0), 'Remise par conditionnement')
                fee = validate_price(line.get('unit_fee', 0), 'Frais par conditionnement')
                if discount > price:
                    raise ValueError('La remise ne peut pas dépasser le prix d’achat.')
                effective = fcfa(price - discount + fee, 'Prix net')
                amount = fcfa(count * effective, 'Total de ligne')
                total += amount
                self.db.add(PurchaseOrderLine(purchase_order_id=order.id, product_id=item.product_id,
                    packaging_id=item.id, packaging_name=item.name, base_unit=item.base_unit,
                    conversion_factor=item.coefficient, allow_fraction=item.allow_fraction,
                    ordered_quantity=count, received_quantity=0, unit_price=price, unit_discount=discount, unit_fee=fee, line_total=amount))
            order.total_amount = fcfa(total, 'Total commande')
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise

    def validate_purchase_order(self, order_id, user_id=None):
        try:
            lock_for_write(self.db)
            order = self.get_purchase_order_by_id(order_id)
            if not order or order.is_cancelled or order.status != 'draft':
                raise ValueError('Seule une commande en brouillon peut être validée.')
            if not order.purchase_order_lines:
                raise ValueError('La commande ne contient aucune ligne.')
            order.status = 'validated'
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def receive_purchase_order(self, order_id, receive_lines_data, user_id=None, request_key=None, due_date=None):
        if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 100:
            raise ValueError('Une clé unique de réception est obligatoire.')
        if not receive_lines_data:
            raise ValueError('La réception doit contenir au moins une ligne.')
        try:
            due_date = validate_date(due_date or None, 'Échéance fournisseur')
            counts = {}
            for data in receive_lines_data:
                line_id = data.get('line_id')
                if not isinstance(line_id, int) or line_id in counts:
                    raise ValueError('Ligne de réception invalide ou répétée.')
                counts[line_id] = quantity(data.get('received_quantity'), 'Quantité reçue')
            lock_for_write(self.db)
            existing = self.db.query(PurchaseReceipt).filter_by(request_key=request_key).first()
            if existing:
                previous = {line.purchase_order_line_id: line.quantity for line in existing.lines}
                debt = self.db.query(SupplierDebt).filter_by(receipt_id=existing.id).first()
                if existing.purchase_order_id == order_id and previous == counts and debt is not None and debt.due_date == due_date:
                    self.db.rollback()
                    return self.db.get(PurchaseReceipt, existing.id)
                raise ValueError('Cette clé de réception a déjà été utilisée.')
            order = self.get_purchase_order_by_id(order_id)
            if not order or order.is_cancelled or order.status not in ('validated', 'partially_received'):
                raise ValueError('La commande doit être validée et non entièrement reçue.')
            receipt = PurchaseReceipt(reference=f'REC-{uuid4().hex.upper()}', request_key=request_key,
                                      purchase_order_id=order.id, total_amount=0)
            self.db.add(receipt)
            self.db.flush()
            total = 0
            for line_id, count in counts.items():
                line = self.db.get(PurchaseOrderLine, line_id)
                if not line or line.purchase_order_id != order.id:
                    raise ValueError('Ligne de commande introuvable.')
                if line.conversion_factor is None or line.base_unit is None or line.allow_fraction is None or line.unit_discount is None or line.unit_fee is None:
                    raise ValueError('Ancienne ligne sans conversion fiable : intervention manuelle requise.')
                if not line.allow_fraction and count != count.to_integral_value():
                    raise ValueError('Ce conditionnement exige une quantité entière.')
                if count > line.ordered_quantity - line.received_quantity:
                    raise ValueError('La quantité reçue dépasse le solde commandé.')
                product = self.db.get(Product, line.product_id)
                if not product or product.unit != line.base_unit:
                    raise ValueError('Unité de base du produit incompatible avec la commande.')
                base_count = quantity(count * line.conversion_factor, 'Quantité de base reçue')
                net_price = fcfa(line.unit_price - line.unit_discount + line.unit_fee, 'Prix net')
                amount = fcfa(count * net_price, 'Montant reçu')
                if product.stock_quantity < 0:
                    raise ValueError('Le coût moyen est indisponible pour un stock négatif.')
                quantity(product.stock_quantity + base_count, 'Stock résultant', allow_zero=True)
                old_stock = Fraction(product.stock_quantity)
                new_stock = old_stock + Fraction(base_count)
                previous_cost = product.average_cost
                # Si un ancien stock a un coût inconnu, ne pas inventer de coût moyen.
                if old_stock == 0 or previous_cost is not None:
                    total_cost = (previous_cost * old_stock if old_stock else Fraction(0)) + amount
                    average = total_cost / new_stock
                    product.average_cost_numerator = str(average.numerator)
                    product.average_cost_denominator = str(average.denominator)
                else:
                    product.average_cost_numerator = product.average_cost_denominator = None
                line.received_quantity += count
                self.db.add(PurchaseReceiptLine(receipt_id=receipt.id, purchase_order_line_id=line.id,
                    quantity=count, base_quantity=base_count, unit_price=net_price, amount=amount))
                if not self.stock_service.update_stock(product.id, base_count, 'purchase_reception',
                    unit=line.base_unit, user_id=user_id, reference_document=receipt.reference, commit=False):
                    raise ValueError('Impossible de mettre à jour le stock.')
                total += amount
            receipt.total_amount = fcfa(total, 'Total réception')
            order.received_amount = fcfa(order.received_amount + receipt.total_amount, 'Montant réceptionné')
            supplier = self.db.get(Supplier, order.supplier_id)
            if supplier.balance_due is None or supplier.total_purchases is None:
                raise ValueError('Soldes historiques du fournisseur inconnus : vérification manuelle nécessaire.')
            supplier.balance_due = fcfa(supplier.balance_due + receipt.total_amount, 'Solde fournisseur')
            supplier.total_purchases = fcfa(supplier.total_purchases + receipt.total_amount, 'Total achats fournisseur')
            self.db.add(SupplierDebt(reference=f'DET-{receipt.reference}', supplier_id=supplier.id,
                purchase_order_id=order.id, receipt_id=receipt.id, initial_amount=receipt.total_amount,
                paid_amount=0, remaining_amount=receipt.total_amount, due_date=due_date,
                status='paid' if receipt.total_amount == 0 else 'pending', is_cancelled=False))
            order.status = 'received' if all(line.received_quantity >= line.ordered_quantity for line in order.purchase_order_lines) else 'partially_received'
            self.db.commit()
            self.db.refresh(receipt)
            return receipt
        except Exception:
            self.db.rollback()
            raise

    def cancel_purchase_order(self, order_id, user_id=None):
        try:
            lock_for_write(self.db)
            order = self.get_purchase_order_by_id(order_id)
            if not order or order.is_cancelled or order.status not in ('draft', 'validated'):
                raise ValueError('Une commande déjà réceptionnée ne peut pas être annulée ici.')
            order.is_cancelled = True
            order.status = 'cancelled'
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise


class SupplierPaymentService:
    """Règlements fournisseurs atomiquement liés à une session de trésorerie."""

    def __init__(self, db):
        self.db = db

    def pay(self, debt_id, amount, method, request_key, notes=None, user_id=None, cash_session_id=None):
        if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 100:
            raise ValueError('Une clé unique de règlement est obligatoire.')
        amount = validate_price(amount, 'Montant du règlement')
        if notes is not None and not isinstance(notes, str):
            raise ValueError('Note de règlement invalide.')
        notes = (notes or '').strip() or None
        if notes and len(notes) > 1000:
            raise ValueError('Note de règlement trop longue.')
        if amount <= 0:
            raise ValueError('Montant positif et moyen de paiement valide requis.')
        reference = f'REG-FOUR-{request_key}'
        if not isinstance(cash_session_id, int) or isinstance(cash_session_id, bool):
            raise ValueError('Une session de caisse ouverte est obligatoire.')
        from models.managed_cash import ManagedCashSession, ManagedCashEntry
        from services.managed_cash_service import ManagedCashService
        try:
            lock_for_write(self.db)
            previous = self.db.query(Payment).filter_by(reference=reference).first()
            if previous:
                entry = self.db.query(ManagedCashEntry).filter_by(supplier_payment_id=previous.id).first()
                if (previous.supplier_debt_id == debt_id and previous.amount == amount and previous.payment_method == method
                        and previous.notes == notes and entry and entry.session_id == cash_session_id and entry.amount == amount and entry.method == method):
                    previous_id = previous.id
                    self.db.rollback()
                    return self.db.get(Payment, previous_id)
                raise ValueError('Cette clé de règlement a déjà été utilisée.')
            from services.cash_methods import require_active
            require_active(self.db, method)
            session = self.db.get(ManagedCashSession, cash_session_id)
            if not session or session.status != 'open':
                raise ValueError('Une session de caisse ouverte est obligatoire.')
            if method == 'cash' and ManagedCashService(self.db).cash_available(session) < amount:
                raise ValueError('Espèces insuffisantes dans la caisse.')
            debt = self.db.get(SupplierDebt, debt_id)
            if not debt or debt.is_cancelled or debt.receipt_id is None:
                raise ValueError('Dette de réception introuvable ou historique non rapprochée.')
            if debt.remaining_amount is None or amount > debt.remaining_amount:
                raise ValueError('Le règlement dépasse le solde de la dette.')
            supplier = self.db.get(Supplier, debt.supplier_id)
            if supplier.balance_due is None or supplier.balance_due < amount:
                raise ValueError('Solde fournisseur incohérent : vérification manuelle nécessaire.')
            payment = Payment(reference=reference, supplier_debt_id=debt.id, amount=amount,
                              payment_method=method, cash_link_status='linked_cash', notes=notes, user_id=user_id)
            self.db.add(payment)
            self.db.flush()
            self.db.add(ManagedCashEntry(session_id=session.id, supplier_payment_id=payment.id, method=method, amount=amount))
            debt.paid_amount = fcfa(debt.paid_amount + amount, 'Total réglé')
            debt.remaining_amount = fcfa(debt.remaining_amount - amount, 'Reste à payer')
            debt.status = 'paid' if debt.remaining_amount == 0 else 'partial'
            supplier.balance_due = fcfa(supplier.balance_due - amount, 'Solde fournisseur')
            self.db.commit()
            self.db.refresh(payment)
            return payment
        except Exception:
            self.db.rollback()
            raise
