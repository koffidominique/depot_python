"""Annulation totale des ventes au comptant ou à crédit du nouveau circuit."""
from fractions import Fraction
from models.managed_cash import ManagedCashSession
from models.managed_operations import (ManagedSale, ManagedSaleLine, ManagedCashTransaction,
                                       ManagedSalePayment, ManagedSaleCancellation, ManagedSaleRefund)
from models.product import Product
from models.managed_deposit import ManagedDepositIssue, ManagedDepositReturn, ManagedDepositReturnCancellation
from models.returnable_stock import ReturnableStockBalance, ReturnableStockMovement
from services.returnable_stock_service import MAX_QUANTITY
from models.managed_credit import ManagedCreditSale
from models.managed_returns import ManagedReturn, ManagedReturnCancellation
from money import fcfa
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService, _key
from services.packaging_service import quantity
from services.sqlite_transaction import lock_for_write
from services.stock_service import StockService


class SaleCancellationService:
    def __init__(self, db):
        self.db = db

    def cancel(self, sale_id, session_id, reason, request_key, *, goods_recovered=False, empties_recovered=False):
        key = _key(request_key)
        if goods_recovered is not True:
            raise ValueError('Confirmez que tous les produits vendus ont été récupérés en stock.')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        try:
            lock_for_write(self.db)
            METHODS = labels(self.db)
            previous = self.db.query(ManagedSaleCancellation).filter_by(request_key=key).first()
            if previous:
                if (previous.sale_id, previous.session_id, previous.reason) == (sale_id, session_id, reason):
                    ident = previous.id
                    self.db.rollback()
                    return self.db.get(ManagedSaleCancellation, ident)
                raise ValueError('Cette clé d’annulation a déjà été utilisée.')
            sale = self.db.get(ManagedSale, sale_id)
            session = self.db.get(ManagedCashSession, session_id)
            if not sale:
                raise ValueError('Vente introuvable.')
            if not session or session.status != 'open':
                raise ValueError('Une caisse ouverte est obligatoire pour les remboursements.')
            if self.db.query(ManagedSaleCancellation).filter_by(sale_id=sale.id).first():
                raise ValueError('Cette vente est déjà annulée.')
            if (self.db.query(ManagedReturn.id).outerjoin(ManagedReturnCancellation, ManagedReturnCancellation.return_id == ManagedReturn.id)
                .filter(ManagedReturn.sale_id == sale.id, ManagedReturnCancellation.id.is_(None)).first()):
                raise ValueError('Un retour partiel existe déjà : annulation totale indisponible, utilisez les retours restants.')
            issues = self.db.query(ManagedDepositIssue).join(ManagedSaleLine, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).filter(ManagedSaleLine.sale_id == sale.id).all()
            if issues and empties_recovered is not True:
                raise ValueError('Confirmez la récupération physique de tous les emballages consignés.')
            if issues and self.db.query(ManagedDepositReturn.id).join(ManagedDepositIssue, ManagedDepositIssue.id == ManagedDepositReturn.issue_id).join(
                    ManagedSaleLine, ManagedSaleLine.id == ManagedDepositIssue.sale_line_id).outerjoin(ManagedDepositReturnCancellation,
                    ManagedDepositReturnCancellation.return_id == ManagedDepositReturn.id).filter(
                    ManagedSaleLine.sale_id == sale.id, ManagedDepositReturnCancellation.id.is_(None)).first():
                raise ValueError('Un retour de vides actif existe déjà : annulation totale indisponible.')
            totals = {}
            for issue in issues:
                if issue.pieces <= 0 or issue.unit_value < 0 or issue.amount != fcfa(issue.pieces * issue.unit_value):
                    raise ValueError('Consigne historique incohérente.')
                totals[issue.returnable_id] = totals.get(issue.returnable_id, 0) + issue.pieces
            for ident, count in totals.items():
                balance = self.db.get(ReturnableStockBalance, ident)
                if not balance or balance.quantity < 0 or balance.quantity + count > MAX_QUANTITY:
                    raise ValueError('Stock initial de vides obligatoire et stock résultant valide.')
            lines = self.db.query(ManagedSaleLine).filter_by(sale_id=sale.id).order_by(ManagedSaleLine.id).all()
            if not lines or fcfa(sum(line.amount for line in lines) + sum(issue.amount for issue in issues), 'Total des lignes') != sale.total:
                raise ValueError('Historique des lignes incohérent : diagnostic requis.')
            links = self.db.query(ManagedSalePayment).filter_by(sale_id=sale.id).all()
            credit = self.db.query(ManagedCreditSale).filter_by(sale_id=sale.id).one_or_none()
            if sale.payment_method == 'credit':
                if not credit or not 0 <= credit.remaining_amount <= credit.initial_amount <= sale.total:
                    raise ValueError('Créance incohérente : diagnostic requis.')
                originals = [self.db.get(ManagedCashTransaction, item.transaction_id) for item in links]
                expected_paid = sale.total - credit.remaining_amount
            elif sale.payment_method == 'mixed' and credit is None:
                if len(links) < 2:
                    raise ValueError('Paiements mixtes incomplets : diagnostic requis.')
                originals = [self.db.get(ManagedCashTransaction, item.transaction_id) for item in links]
                expected_paid = sale.total
            elif sale.payment_method in METHODS and not links and credit is None:
                originals = self.db.query(ManagedCashTransaction).filter_by(sale_id=sale.id, kind='sale').all()
                if len(originals) != 1 or originals[0].method != sale.payment_method:
                    raise ValueError('Paiement de la vente incohérent : diagnostic requis.')
                expected_paid = sale.total
            else:
                raise ValueError('Ce type de vente ne peut pas être annulé par cette procédure.')
            if (any(not entry or entry.method not in METHODS or entry.amount <= 0 or
                    (entry.kind, entry.sale_id) not in (('sale', sale.id), ('income', None)) for entry in originals)
                    or sum(entry.sale_id == sale.id for entry in originals) > 1
                    or (sale.payment_method != 'credit' and sum(entry.sale_id == sale.id for entry in originals) != 1)
                    or fcfa(sum(entry.amount for entry in originals), 'Total encaissé') != expected_paid):
                raise ValueError('Encaissements incohérents : diagnostic requis.')
            direct = self.db.query(ManagedCashTransaction).filter_by(sale_id=sale.id).all()
            if any(entry.id not in {original.id for original in originals} for entry in direct):
                raise ValueError('Encaissements incohérents : diagnostic requis.')
            cash_refund = fcfa(sum(entry.amount for entry in originals if entry.method == 'cash'), 'Remboursement espèces')
            if cash_refund > ManagedCashService(self.db).cash_available(session):
                raise ValueError('Espèces insuffisantes pour le remboursement.')
            cancellation = ManagedSaleCancellation(sale_id=sale.id, session_id=session.id, request_key=key, reason=reason)
            self.db.add(cancellation)
            if credit is not None:
                credit.remaining_amount = 0
            self.db.flush()
            reference = f'ANNULATION-{cancellation.id}'
            for ident, count in totals.items():
                balance = self.db.get(ReturnableStockBalance, ident)
                before = balance.quantity
                balance.quantity += count
                self.db.add(ReturnableStockMovement(request_key=f'annulation-vente-vides:{cancellation.id}:{ident}',
                    packaging_id=ident, movement_type='entry', quantity=count, stock_before=before,
                    stock_after=balance.quantity, reason=reason, reference_document=reference))
            for line in lines:
                product = self.db.get(Product, line.product_id)
                if not product or product.unit != line.base_unit or product.stock_quantity is None or product.stock_quantity < 0:
                    raise ValueError('Stock ou unité du produit incohérent : diagnostic requis.')
                restored = quantity(line.base_quantity, 'Quantité récupérée')
                before = product.stock_quantity
                quantity(before + restored, 'Stock résultant', allow_zero=True)
                current_cost = product.average_cost if before else None
                if line.cost_numerator is None and line.cost_denominator is None:
                    original_cost = None
                elif line.cost_numerator is None or line.cost_denominator is None:
                    raise ValueError('Coût historique incomplet.')
                else:
                    numerator, denominator = int(line.cost_numerator), int(line.cost_denominator)
                    if numerator < 0 or denominator <= 0:
                        raise ValueError('Coût historique invalide.')
                    original_cost = Fraction(numerator, denominator)
                if original_cost is None or (before and current_cost is None):
                    product.average_cost_numerator = product.average_cost_denominator = None
                else:
                    value = (Fraction(before) * (current_cost or 0) + Fraction(restored) * original_cost) / Fraction(before + restored)
                    product.average_cost_numerator, product.average_cost_denominator = str(value.numerator), str(value.denominator)
                if not StockService(self.db).update_stock(product.id, restored, 'sale_cancellation', unit=product.unit,
                                                           reason=reason, reference_document=reference, commit=False):
                    raise ValueError('Rétablissement du stock impossible.')
            for original in originals:
                refund = ManagedCashTransaction(session_id=session.id, request_key=f'remboursement:{cancellation.id}:{original.id}',
                    kind='outflow', method=original.method, amount=original.amount,
                    description=f'Remboursement {sale.reference} — {reason}', reference=reference)
                self.db.add(refund)
                self.db.flush()
                self.db.add(ManagedSaleRefund(cancellation_id=cancellation.id, original_transaction_id=original.id,
                                               refund_transaction_id=refund.id))
            self.db.commit()
            self.db.refresh(cancellation)
            return cancellation
        except Exception:
            self.db.rollback()
            raise
